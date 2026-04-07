import gradio as gr
from dotenv import load_dotenv
#from research_manager import ResearchManager
from deep_research_manager import DeepResearchManager

load_dotenv(override=True)


# single global manager instance so that its state could persist between user inputs
manager = DeepResearchManager()
# but for multiple users, they cannot share the same state, so you need to use session state /gr.State to pass state explicitly
async def run(query: str):

    manager.pending_email_delivery  = False
    clarification_needed = False
    status_text = ""
    full_report = ""    

    async for chunk in manager.run(query):
        
        if chunk["type"] == "status":
            status_text  = chunk["content"] # replace text if it's a status update
        elif chunk["type"] == "report":
            full_report += chunk["content"] # append if it's the final report
        elif chunk["type"] == "clarification":
            status_text  = chunk["content"]
            clarification_needed = True
        
        
        #debug meaning “Print the chunk, but if it’s a string, only show the first 80 characters, and show it in a way where I can see hidden characters.”
        #print("streaming chunk:", repr(chunk[:80]) if isinstance(chunk, str) else chunk)

        yield (
            gr.update(interactive=False),
            status_text,
            full_report,
            gr.update(visible=True), # these matches the position/order of gr components defined in outputs[]
            gr.update(visible=True, interactive=False)
        )
        # if waiting for clarification answers, need to exit the loop and function
        if clarification_needed:
            yield (
                gr.update(interactive=True),
                status_text,
                full_report,
                gr.update(visible=True), # these matches the position/order of gr components defined in outputs[]
                gr.update(visible=True, interactive=False)
            )
            return

    print("FINAL pending_email_delivery:", manager.pending_email_delivery)
    # after streaming finishes, show email options
    show_email_option = bool(manager.pending_email_delivery)
    yield (
        gr.update(interactive=False),
        "Deep Research Done!",
        full_report,
        gr.update(visible=show_email_option),
        gr.update(visible=show_email_option, interactive = True)
    )
    

#send email
async def send_email_ui(email, report):
    yield (
        gr.update(value="Sending...", interactive=False),
        "Sending..."
    )
    
    await manager.send_email(email, report)

    yield (
        gr.update(value="Report sent!", interactive=True),
        "Report Sent!"
    )

# gr.Blocks(..) allow more customized layouts/event handling...
with gr.Blocks(theme=gr.themes.Default(primary_hue="amber", text_size="lg")) as ui:
    gr.Markdown("# 🏄🏻 Deep Research Report Generator") #heading
    query_textbox = gr.Textbox(label="What topic would you like to research?") #what the user sees
    with gr.Row():
        run_button = gr.Button("Run", variant="primary")
        clear_button = gr.Button("Clear") 

    status = gr.Markdown(label="Status")
    report = gr.Markdown(label="Report")
    email_textbox = gr.Textbox(label="If you'd like to get the report via email, please enter your email below:", visible=False)
    send_email_button = gr.Button("Send report now", visible=False)
    # event handling
    # call the callback "run" when run button is clicked or if user pressed "Enter" while inside the textbox
    run_button.click(fn=run, inputs=query_textbox, outputs=[run_button, status, report, email_textbox, send_email_button])
    #query_textbox.submit(fn=run, inputs=query_textbox, outputs=[status, report, email_textbox, send_email_button])

    clear_button.click(
        fn=lambda:("", gr.update(interactive=True), "", gr.update(visible=False), gr.update(value="Send report now",visible=False), ""),
        outputs=[query_textbox, run_button, status, email_textbox, send_email_button, report]
        )
    send_email_button.click(fn=send_email_ui, inputs=[email_textbox, report], outputs=[send_email_button, status])
    #email_textbox.submit(fn=send_email_ui, inputs=[email_textbox, report], outputs=[send_email_button, status])

if __name__ == "__main__":
    ui.launch(inbrowser=True)


