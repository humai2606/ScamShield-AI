
if st.button(
    "🔍 Investigate Message",
    type="primary",
    use_container_width=True
):
    if not message.strip():
        st.warning("Please enter a message before investigation.")

    else:
        with st.spinner("ScamShield AI is analyzing your message..."):
            try:
                report = investigate_message(message)
                report["message"] = message
                report["date"] = datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                )

                st.session_state.history.append(report)
                st.session_state.latest_report = report

                st.success("Investigation completed successfully!")
                st.rerun()

            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the AI service. "
                    "Check whether Ollama is running or whether "
                    "your Groq API key is configured."
                )

            except requests.exceptions.Timeout:
                st.error(
                    "The AI service took too long to respond. "
                    "Please try again."
                )

            except Exception as error:
                st.error(f"Something went wrong: {error}")
