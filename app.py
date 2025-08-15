import streamlit as st
from openai import OpenAI

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Pocket Doctor - Your AI Medical Assistant",
    page_icon="./assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "This app uses Google's Gemini AI to provide medical consultations. "},
)

st.markdown("""
    <style>
    header, footer { 
        visibility: hidden; 
        height: 1px; 
        padding: 0; 
        margin: 0; 
    }
    .block-container {
        padding-top: 3%;
        padding-bottom: 5%;
        padding-left: 10%;
        padding-right: 10%;
    }
    h1 {
        color: var(--text-color); /* Theme-aware color */
        font-weight: bold;
    }
            
    @media (max-width: 640px) {
        .stColumn > div {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            padding-top: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Two columns for logo and title
col1, col2 = st.columns([1, 8])  # 1:6 width ratio

with col1:
    st.image("assets/logo.png", width=60)

with col2:
    st.markdown("<center><h1>Pocket Doctor</h1></center>", unsafe_allow_html=True)



# --- OPENAI CLIENT ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- CHAT FUNCTION ---
def get_openai_response(messages):
    openai_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=openai_messages
    )
    return response.choices[0].message.content

# --- FORM FOR USER DETAILS ---
def symptom_form():
    # Custom CSS to style the Streamlit form itself
    st.markdown("""
        <style>
        /* Target our form by its form ID */
        div[data-testid="stForm"] {
            border: 2px solid #000;      /* Black border */
            border-radius: 12px;         /* Rounded corners */
            padding: 25px;
            background-color: rgba(255, 255, 255, 0); /* Transparent */
        }

        /* Fix textarea height with scrollbar */
        textarea {
            resize: none !important;
            overflow-y: auto !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("### Enter Your Details")
    # This form will now get the border because we target stForm in CSS
    with st.form("patient_form", clear_on_submit=True):
        age = st.number_input("Age", min_value=1, max_value=120, step=1)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        concerns = st.text_area("Describe your main health concerns", 
                                       help="List down your main health concerns or issues along with your medical history in at least 10 words.",
                                       placeholder="Here you can describe your main health concerns or issues along with your medical history, medications you are on, any allergies, and any other relevant information. The more details you provide, the better the Doctor can assist you.",
                                       )
        submit = st.form_submit_button("Start Consultation")
        if submit:
            if not concerns.strip(): 
                st.error("❌ Please enter your health concerns before starting your e-consultation.")
                return
            if len(concerns.strip().split()) < 10: 
                st.error("❌ Please describe your health concerns in at least 10 words to ensure the doctor has enough information to assist you.")
                return
            
            st.session_state['user_data'] = {
                "age": age,
                "gender": gender,
                "health_concerns": concerns,
            }
            st.session_state['consult_started'] = True
            st.session_state['chat_history'] = []

            # Automatically get first response
            initial_prompt = (f"""
                You are a highly experienced medical doctor. The patient is\
                {age} years old, {gender}\
                Medical history and Patient Concerns: {concerns}\
                Ask follow-up questions if needed. Provide dianoses, potential causes, and recommendations for improvements.\
                Do not bombard the patient with questions and excessive medical jargon.\
                Always respond in a professional and empathetic manner.
                Provide potential causes and recommendation for improvements.
                If you need more information, ask the patient directly.
                At no point should you say "I am not a doctor" or "I cannot provide medical advice.
                The patient should not feel that he is talking to an AI to give him a sense of trust.
                """
            )

            patient_summary = (
                f"Patient Summary: \n"
                f"- Age: {age} years\n"
                f"- Gender: {gender}\n"
                f"- Health Concerns: {concerns}\n"
            )

            # st.session_state['chat_history'].append({"role": "user", "content": initial_prompt})
            st.session_state['chat_history'].append({"role": "user", "content": patient_summary})
            with st.spinner("Curating the best advice for your needs"):
                # Get the first response from Gemini
                bot_first_response = get_openai_response([{"role": "user", "content": initial_prompt}])
                st.session_state['chat_history'].append({"role": "assistant", "content": bot_first_response})
            st.rerun()

if 'user_data' not in st.session_state:
    symptom_form()


# --- CHAT INTERFACE ---
if st.session_state.get('consult_started'):
    st.markdown("#### Doctor Consultation")
    for msg in st.session_state['chat_history']:
        with st.chat_message("user" if msg["role"]=="user" else "assistant"):
            st.markdown(f"<div class='transparent-box'>{msg['content']}</div>", unsafe_allow_html=True)

    user_message = st.chat_input("Enter your query...")
    if user_message:
        st.session_state['chat_history'].append({"role": "user", "content": user_message})
        with st.spinner("Doctor is thinking..."):
            bot_response = get_openai_response(st.session_state['chat_history'])
        st.session_state['chat_history'].append({"role": "assistant", "content": bot_response})
        st.rerun()

    if st.button("🔄 Start Over"):
        for key in ("user_data", "consult_started", "chat_history"):
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
