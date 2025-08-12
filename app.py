import streamlit as st
from openai import OpenAI

# --- PAGE SETUP ---
st.set_page_config(
    page_title="DocAI - Your AI Medical Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "This app uses Google's Gemini AI to provide medical consultations. "},
)

st.markdown("""
    <h1 style='text-align: center; color: black; font-weight: bold;'>
        DocAI
    </h1>
    <style>
    .block-container {
        padding-top: 5%;
        padding-bottom: 5%;
        padding-left: 10%;
        padding-right: 10%;
    }

    </style>
""", unsafe_allow_html=True)



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
        medical_history = st.text_area("Existing conditions", 
                                       help="List any existing medical conditions or surgeries",
                                       placeholder="e.g., diabetes, hypertension, previous surgeries",
                                       height=10)
        medications = st.text_area("Current medications",
                                   help="List any medications you are currently taking",
                                   placeholder="e.g., aspirin, metformin", 
                                   height=10)
        allergies = st.text_area("Allergies",
                                 help="List any known allergies",
                                 placeholder="e.g., penicillin, peanuts", 
                                 height=10)
        symptoms = st.text_area("Describe your symptoms",
                                 help="Describe your current symptoms in detail",
                                 placeholder="e.g., fever, cough, pain", 
                                 height=10)

        submit = st.form_submit_button("Start Consultation")
        if submit:
            if not age or age < 1 or age > 120:
                st.error("❌ Please enter a valid age between 1 and 120.")
                return
            if not symptoms.strip(): 
                st.error("❌ Please enter your symptoms before consultation.")
                return
            
            st.session_state['user_data'] = {
                "age": age,
                "gender": gender,
                "medical_history": medical_history,
                "medications": medications,
                "allergies": allergies,
                "symptoms": symptoms
            }
            st.session_state['consult_started'] = True
            st.session_state['chat_history'] = []

            # Automatically get first response
            initial_prompt = (f"""
                You are a highly experienced medical doctor. The patient is\
                {age} years old, {gender}\
                Medical history: {medical_history}\
                Current medications: {medications}\
                Allergies: {allergies}\
                Symptoms: {symptoms}\
                Ask follow-up questions if needed, give a probable diagnosis, and detailed treatment advice
                Always respond in a professional and empathetic manner.
                Provide a summary of the patient's condition and recommended next steps.
                If you need more information, ask the patient directly.
                At no point should you say "I am not a doctor" or "I cannot provide medical advice.
                The patient should not feel that he is talking to an AI to give him a sense of trust.
                """
            )

            patient_summary = (
                f"Patient Summary: \n"
                f"- Age: {age} years\n"
                f"- Gender: {gender}\n"
                f"- Medical history: {medical_history if medical_history.strip() else 'None'}\n"
                f"- Current medications: {medications if medications.strip() else 'None'}\n"
                f"- Allergies: {allergies if allergies.strip() else 'None'}\n"
                f"- Symptoms: {symptoms}"
            )

            # st.session_state['chat_history'].append({"role": "user", "content": initial_prompt})
            st.session_state['chat_history'].append({"role": "user", "content": patient_summary})
            with st.spinner("Looking for the best doctor..."):
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
