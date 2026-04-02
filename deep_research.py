import gradio as gr
from dotenv import load_dotenv
#from research_manager import ResearchManager
from deep_research_manager import DeepResearchManager

load_dotenv(override=True)


# single global manager instance so that its state could persist between user inputs
manager = DeepResearchManager()
# but for multiple users, they cannot share the same state, so you need to use session state /gr.State to pass state explicitly
async def run(query: str):
    async for chunk in manager.run(query):
        yield chunk # stream each chunk of result generated

# gr.Blocks(..) allow more customized layouts/event handling...
with gr.Blocks(theme=gr.themes.Default(primary_hue="amber", text_size="lg")) as ui:
    gr.Markdown("# Deep Research") #heading
    query_textbox = gr.Textbox(label="What topic would you like to research?") #what the user sees
    with gr.Row():
        run_button = gr.Button("Run", variant="primary")
        clear_button = gr.Button("Clear")
    report = gr.Markdown(label="Report")
    
    # event handling
    # call the callback "run" when run button is clicked
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    # or if user pressed "Enter" while inside the textbox
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

    clear_button.click(fn=lambda:"", outputs=query_textbox)

ui.launch(inbrowser=True)

