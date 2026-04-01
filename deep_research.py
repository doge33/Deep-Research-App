import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk # stream each chunk of result generated

# gr.Blocks(..) allow more customized layouts/event handling...
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research") #heading
    query_textbox = gr.Textbox(label="What topic would you like to research?") #what the user sees
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    # event handling
    # call the callback "run" when run button is clicked
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    # or if user pressed "Enter" while inside the textbox
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)

