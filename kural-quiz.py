import streamlit as st
import random
import time
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, util
import torch

# Load dataset (cached by HuggingFace after first load)
@st.cache_data
def load_thirukural():
    dataset = load_dataset("Selvakumarduraipandian/Thirukural")
    return dataset["train"]

# Load SentenceTransformer model (cached)
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

# Generate semantic distractors for MCQs
def get_distractors(model, all_data, correct_text, column, top_k=3):
    corpus = [x[column] for x in all_data if x[column] != correct_text]
    embeddings = model.encode(corpus, convert_to_tensor=True)
    query_emb = model.encode(correct_text, convert_to_tensor=True)
    hits = util.semantic_search(query_emb, embeddings, top_k=top_k)[0]
    distractors = [corpus[hit['corpus_id']] for hit in hits]
    return distractors

# Generate a question with semantic options
def generate_question(entry, all_data, model, number_column):
    q_type = random.choice(["number", "meaning", "adhigaram"])
    
    if q_type == "number":
        question = f"Identify the number of this Thirukkural:\n\n{entry['Kural']}"
        correct = str(entry[number_column])
        options = random.sample([str(x[number_column]) for x in all_data if x[number_column] != entry[number_column]], 3)
        options.append(correct)
        random.shuffle(options)
        return question, options, correct

    elif q_type == "meaning":
        question = f"What is the correct meaning of this Thirukkural?\n\n{entry['Kural']}"
        correct = entry["Vilakam"]
        distractors = get_distractors(model, all_data, correct, "Vilakam", top_k=3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, options, correct

    elif q_type == "adhigaram":
        question = f"This Thirukkural belongs to which Adhigaram?\n\n{entry['Kural']}"
        correct = entry["Adhigaram"]
        distractors = get_distractors(model, all_data, correct, "Adhigaram", top_k=3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, options, correct

# ------------------ STREAMLIT APP ------------------

st.set_page_config(page_title="Thirukkural Quiz", layout="centered")

# Header with creator details
st.title("📜 Thirukkural Quiz")
st.markdown("---")

# Creator info in sidebar
with st.sidebar:
    st.markdown("### 👨‍💻 Creator")
    st.markdown("**Selvakumar Duraipandian**")
    st.markdown("[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/selvakumarduraipandian)")
    st.markdown("---")
    
# Also show creator info in main area (smaller)
col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("""""", unsafe_allow_html=True)

# Load data and model
data = load_thirukural()
model = load_model()

# Debug: Show available columns
if "columns_checked" not in st.session_state:
    st.session_state.columns_checked = True
    sample_entry = data[0]
    # st.write("**Debug Info - Available columns:**", list(sample_entry.keys()))
    
    # Try to find the number column
    number_column = None
    for col in ['number', 'Number', 'Kural_Number', 'id', 'ID']:
        if col in sample_entry:
            number_column = col
            break
    
    if number_column:
        # st.success(f"Found number column: '{number_column}'")
        st.session_state.number_column = number_column
    else:
        st.error("Could not find a number column. Please check the column names above.")
        st.stop()

if "score" not in st.session_state:
    st.session_state.score = 0
    st.session_state.q_no = 0
    st.session_state.total_qs = 0
    st.session_state.current_q = None
    st.session_state.correct = None
    st.session_state.show_result = False
    st.session_state.user_answer = None

# Start quiz setup
if st.session_state.total_qs == 0:
    st.subheader("Start your Quiz")
    total = st.number_input("How many questions do you want to try?", min_value=1, max_value=20, value=5, step=1)
    if st.button("Start Quiz"):
        st.session_state.total_qs = total
        st.session_state.q_no = 1
        entry = random.choice(data)
        q, options, correct = generate_question(entry, data, model, st.session_state.number_column)
        st.session_state.current_q = (q, options)
        st.session_state.correct = correct
        st.rerun()

# Quiz in progress
elif st.session_state.q_no <= st.session_state.total_qs:
    q, options = st.session_state.current_q
    correct = st.session_state.correct

    # Show progress
    st.progress(st.session_state.q_no / st.session_state.total_qs)
    st.markdown(f"**Question {st.session_state.q_no} of {st.session_state.total_qs}** | **Score: {st.session_state.score}/{st.session_state.q_no-1}**" if st.session_state.q_no > 1 else f"**Question {st.session_state.q_no} of {st.session_state.total_qs}**")

    st.markdown(f"### {q}")

    # Show result if answer was submitted
    if st.session_state.show_result:
        if st.session_state.user_answer == correct:
            st.success("✅ Correct! Well done!")
        else:
            st.error(f"❌ Wrong!")
            st.info(f"**Correct answer:** {correct}")
            
        # Show delay message and wait
        with st.spinner("Next question loading in 3 seconds..."):
            time.sleep(3)
        
        # Move to next question
        st.session_state.q_no += 1
        st.session_state.show_result = False
        st.session_state.user_answer = None
        
        if st.session_state.q_no <= st.session_state.total_qs:
            entry = random.choice(data)
            q, options, correct = generate_question(entry, data, model, st.session_state.number_column)
            st.session_state.current_q = (q, options)
            st.session_state.correct = correct
        st.rerun()
    
    else:
        # Show question and options
        answer = st.radio("Choose an answer:", options, key=f"q{st.session_state.q_no}")

        if st.button("Submit Answer", type="primary"):
            st.session_state.user_answer = answer
            if answer == correct:
                st.session_state.score += 1
            st.session_state.show_result = True
            st.rerun()

# Quiz finished
else:
    # Calculate percentage
    percentage = round((st.session_state.score / st.session_state.total_qs) * 100)
    
    st.balloons()  # Celebration animation
    st.success(f"🎉 Quiz Completed!")
    
    # Results display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{st.session_state.score}/{st.session_state.total_qs}")
    with col2:
        st.metric("Percentage", f"{percentage}%")
    with col3:
        if percentage >= 80:
            st.metric("Grade", "Excellent! 🌟")
        elif percentage >= 60:
            st.metric("Grade", "Good! 👍")
        else:
            st.metric("Grade", "Keep Learning! 📚")
    
    # Motivational message
    if percentage == 100:
        st.markdown("### 🏆 Perfect Score! You're a Thirukkural Master!")
    elif percentage >= 80:
        st.markdown("### 🌟 Excellent work! You know your Thirukkural well!")
    elif percentage >= 60:
        st.markdown("### 👍 Good job! Keep exploring more Thirukkural wisdom!")
    else:
        st.markdown("### 📚 Great start! Practice more to improve your knowledge!")
    
    if st.button("🔄 Play Again", type="primary"):
        st.session_state.score = 0
        st.session_state.q_no = 0
        st.session_state.total_qs = 0
        st.session_state.current_q = None
        st.session_state.correct = None
        st.session_state.show_result = False
        st.session_state.user_answer = None
        st.rerun()