import streamlit as st
import random
import time
from datasets import load_dataset

# Load dataset (cached by HuggingFace after first load)
@st.cache_data
def load_thirukural():
    dataset = load_dataset("Selvakumarduraipandian/Thirukural")
    return dataset["train"]

# Generate random distractors (simpler approach without ML)
def get_random_distractors(all_data, correct_text, column, count=3):
    options = [x[column] for x in all_data if x[column] != correct_text]
    return random.sample(options, min(count, len(options)))

# Generate a question (updated with more types based on dataset columns)
def generate_question(entry, all_data):
    q_type = random.choice(["meaning", "adhigaram", "paal", "iyal", "couplet", "kalaingar_urai", "word_context"])
    
    kural_html = entry['Kural']
    
    if q_type == "meaning":
        question = f"What is the correct meaning of this Thirukkural?"
        correct = entry["Vilakam"]
        distractors = get_random_distractors(all_data, correct, "Vilakam", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

    elif q_type == "adhigaram":
        question = f"This Thirukkural belongs to which Adhigaram?"
        correct = entry["Adhigaram"]
        distractors = get_random_distractors(all_data, correct, "Adhigaram", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

    elif q_type == "paal":
        question = f"This Thirukkural belongs to which Paal?"
        correct = entry["Paal"]
        distractors = get_random_distractors(all_data, correct, "Paal", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

    elif q_type == "iyal":
        question = f"This Thirukkural belongs to which Iyal?"
        correct = entry["Iyal"]
        distractors = get_random_distractors(all_data, correct, "Iyal", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

    elif q_type == "couplet":
        question = f"What is the English Couplet for this Thirukkural?"
        correct = entry["Couplet"]
        distractors = get_random_distractors(all_data, correct, "Couplet", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

    elif q_type == "kalaingar_urai":
        question = f"What is Kalaingar's Urai for this Thirukkural?"
        correct = entry["Kalaingar_Urai"]
        distractors = get_random_distractors(all_data, correct, "Kalaingar_Urai", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

    elif q_type == "word_context":
        # Pick a random word from Kural (split by spaces, ignore punctuation)
        words = entry['Kural'].replace('<br />', ' ').split()
        word = random.choice(words)
        question = f"What is the contextual role or related phrase for the word '{word}' in this Thirukkural? (Based on Vilakam)"
        # Approximate "meaning" by finding a phrase in Vilakam (or use full Vilakam as correct; distractors from other Vilakams)
        correct = entry["Vilakam"]  # Full Vilakam as proxy; could parse for word if needed
        distractors = get_random_distractors(all_data, correct, "Vilakam", 3)
        options = distractors + [correct]
        random.shuffle(options)
        return question, kural_html, options, correct

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
    
# Load data
try:
    data = load_thirukural()
    
except Exception as e:
    st.error(f"Failed to load dataset: {str(e)}")
    st.info("Please check if the dataset name 'Selvakumarduraipandian/Thirukural' is correct.")
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
        q, kural_html, options, correct = generate_question(entry, data)
        st.session_state.current_q = (q, kural_html, options)
        st.session_state.correct = correct
        st.rerun()

# Quiz in progress
elif st.session_state.q_no <= st.session_state.total_qs:
    q, kural_html, options = st.session_state.current_q
    correct = st.session_state.correct

    # Show progress
    st.progress(st.session_state.q_no / st.session_state.total_qs)
    st.markdown(f"**Question {st.session_state.q_no} of {st.session_state.total_qs}** | **Score: {st.session_state.score}/{st.session_state.q_no-1}**" if st.session_state.q_no > 1 else f"**Question {st.session_state.q_no} of {st.session_state.total_qs}**")

    # Display question
    st.markdown(f"### {q}")
    
    # Display Kural with proper HTML rendering and styling
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-size: 1.2em;
        font-weight: 500;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    '>
        {kural_html}
    </div>
    """, unsafe_allow_html=True)

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
            q, kural_html, options, correct = generate_question(entry, data)
            st.session_state.current_q = (q, kural_html, options)
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
    # Show YouTube meme video if score is zero, otherwise show markdown message
    if st.session_state.score == 0:
        # Example: Vadivelu comedy clip (replace with your preferred YouTube video)
        youtube_embed_url = "https://www.youtube.com/embed/3h7iUEBP7XQ"  # Replace with actual YouTube embed URL
        st.markdown(
            f"""
            <div style='text-align: center;'>
                <h4>Oops, no points! Here's a meme to cheer you up! 😄</h4>
                <iframe width="560" height="315" src="{youtube_embed_url}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
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