import streamlit as st
import backend
import pandas as pd
import PyPDF2

st.set_page_config(page_title="AI-Pass", page_icon="🤖", layout="wide")


def extract_text_from_pdf(uploaded_file):
    uploaded_file.seek(0)
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text() or ""
        text += page_text + "\n"
    return text.strip()


def csv_to_prompt_text(df):
    numeric_summary = df.select_dtypes(include="number").describe().round(2)
    preview = df.head(5).to_string(index=False)
    summary = numeric_summary.to_string() if not numeric_summary.empty else "No numeric columns found."
    return (
        "Analyze this CSV data:\n"
        f"{preview}\n\n"
        f"CSV shape: {df.shape}\n\n"
        f"Numeric summary:\n{summary}"
    )


st.title("AI-Pass")
st.markdown("---")

# Sidebar for metadata/status
with st.sidebar:
    st.header("System Status")
    st.info("Pipeline: Active")

    # Debug: API Key status
    import os
    from dotenv import load_dotenv
    import streamlit as st
    load_dotenv()

    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except:
        api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        st.success(f"✓ Gemini API Key loaded ({len(api_key)} chars)")
    else:
        st.error("✗ Gemini API Key NOT found. Add to Streamlit Secrets or .env")
    
    if st.button("Clear Memory"):
        backend.memory.clear()
        st.success("Memory cleared!")
    st.markdown("---")
    st.write("Supported Intents:")
    st.write("- Summarization")
    st.write("- Sentiment Analysis")
    st.write("- Data Analysis")
    st.write("- Anomaly Detection")
    st.write("- Logical Decisions")
    st.write("- Translation")
    st.write("- Code Generation")
    st.write("- Web Search")

# Input Section: Text or File
col_in1, col_in2 = st.columns([1, 1])

with col_in1:
    user_input = st.text_area("Input your request or paste text:", placeholder="e.g., Summarize this report...", height=220)

with col_in2:
    uploaded_file = st.file_uploader("Or upload a document (PDF, CSV)", type=["pdf", "csv"])
    if uploaded_file is not None:
        if uploaded_file.type == "application/pdf":
            with st.spinner("Extracting text from PDF..."):
                file_text = extract_text_from_pdf(uploaded_file)
                if file_text:
                    st.success("PDF loaded successfully!")
                    st.write(f"Extracted {len(file_text)} characters from PDF.")
                    if not user_input:
                        user_input = file_text
                else:
                    st.warning("PDF uploaded, but no text could be extracted.")
        elif uploaded_file.type == "text/csv":
            df = pd.read_csv(uploaded_file)
            st.success("CSV loaded successfully!")
            st.write(f"Data shape: {df.shape}")
            st.dataframe(df.head(), use_container_width=True)
            if not user_input:
                user_input = csv_to_prompt_text(df)
            else:
                st.info("CSV loaded. Add instructions above or use the text area to refine the analysis.")

if st.button("Run System Pipeline", use_container_width=True):
    if user_input:
        with st.spinner("Processing through AI-Pass pipeline..."):
            try:
                response = backend.run_with_memory(user_input)
                intent = response.get("intent")
                if intent == "unknown":
                    st.warning("Couldn't understand that request. Try rephrasing.")
                    error = response.get("error")
                    if error:
                        st.error(f"Error Details: {error}")
                    st.stop()

                result = response.get("result")
                confidence = response.get("confidence", 0)
                steps = response.get("steps", [])

                col1, col2 = st.columns([1, 2])

                with col1:
                    st.subheader("Metadata")
                    st.success(f"**Intent:** {intent}")
                    st.metric("Confidence", f"{confidence * 100:.1f}%")
                    st.write("**Execution Steps:**")
                    for step in steps:
                        st.write(f"- {step}")

                with col2:
                    st.write("### Output")
                    if intent == "generate_code" and isinstance(result, str):
                        st.code(result)
                    elif isinstance(result, dict):
                        st.json(result)
                        if intent == "analyze" and "data_points" in result:
                            data = result["data_points"]
                            if len(data) > 1:
                                st.write("#### Data Visualization")
                                tab1, tab2 = st.tabs(["Line Chart", "Bar Chart"])
                                with tab1:
                                    st.line_chart(data)
                                with tab2:
                                    st.bar_chart(data)
                    else:
                        st.info(result)

                    with st.expander("View Raw Pipeline JSON"):
                        st.json(response)
            except Exception as e:
                st.error(f"Pipeline Error: {e}")
    else:
        st.warning("Please provide input text or upload a file.")

