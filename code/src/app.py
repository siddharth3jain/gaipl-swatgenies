import gradio as gr
import networkx as nx
from controller import llm_response, create_master_data
import plotly.express as px


def generate_chart(df):
    # Convert DataFrame to long format
    df_long = df.melt(id_vars=["incident_id"], var_name="Category", value_name="Value")

    # Create line plot using Plotly
    fig = px.line(df_long, x="incident_id", y="Value", color="Category", markers=True,
                  title="Telemetry chart")

    # Rotate x-axis labels by 90 degrees
    fig.update_layout(xaxis=dict(tickangle=90))

    return fig


# Fetch master data
def generate_gradio_data(input_message:str):
    print("start")
    df_incident_display, df_telemetry_display = create_master_data(input_message)
    print("Finish")
    return df_incident_display, generate_chart(df_telemetry_display)


# Function to reset inputs and outputs
def reset_inputs():
    return "",gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), [], []


def chatbot_response(user_message, chatbot_history):
    if chatbot_history is None:  # Ensure chatbot_history is initialized
        chatbot_history = []

    # Append user message
    chatbot_history.append({"role": "user", "content": user_message})

    # Generate bot response (simple echo for demo)
    bot_response = llm_response(chatbot_history, chatbot_activation=True)
    bot_message = {"role": "assistant", "content": bot_response}

    # Append bot response
    chatbot_history.append(bot_message)

    return chatbot_history, gr.update(value="")  # Clear input box after response


# Create Gradio interface
with gr.Blocks() as demo:
    # Title across the top of the page with background color and centered
    gr.Markdown(
        "# Welcome to Integrated Platform powered by SWAT Genie",
        elem_id="title"
    )

    with gr.Row():  # Create a horizontal layout row for left and right columns
        with gr.Column(scale=1):  # Left column for image display (1/4 of space)
            # Image without bounding box
            image = gr.Image(value=r"./data/logo.jpg",
                             label=None, interactive=False, show_label=False)

        with gr.Column(scale=3):  # Right column for input box and buttons (3/4 of space)
            text_input = gr.Textbox(label="Enter your text", placeholder="Type here...")
            with gr.Row():  # Place buttons side by side
                submit_btn = gr.Button("Submit", size="sm")  # Small size for button
                clear_btn = gr.Button("Clear", size="sm")  # Small size for button

    # Below the input/output section, create another row for the results
    with gr.Row():
        with gr.Column():  # Left column for tabular result
            table_output = gr.DataFrame(label="Similar Incidence", visible=False, interactive=True)

        with gr.Column():  # Right column for text result
            with gr.Group(visible=False) as chatbot_section:
                with gr.Column(elem_id="chatbot-container"):
                    chatbot = gr.Chatbot(label="Chatbot", type='messages')
                    user_input = gr.Textbox(placeholder="Type a message...", label="Chatbot Input")

    with gr.Row():
        with gr.Column(scale=2):
            chart = gr.Plot(label="Telemetry Graph", visible=False, elem_id="custom-chart")

        with gr.Column(scale=2):
            pass

    # When the button is clicked, process input and display results
    submit_btn.click(fn=generate_gradio_data, inputs=text_input, outputs=[table_output, chart])
    # After processing, show the results
    submit_btn.click(
        fn=lambda: [gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)],
        inputs=None,
        outputs=[table_output, chart, chatbot_section])

    # Use gr.State to manage the chat history
    chatbot_history = gr.State([])  # Initialize empty list for chatbot history

    # Clear button functionality
    clear_btn.click(fn=reset_inputs, inputs=None, outputs=[text_input, table_output, chart, chatbot_section, chatbot, chatbot_history])

    # When user submits a message in the chatbot input, show the chatbot and update the history
    user_input.submit(fn=chatbot_response, inputs=[user_input, chatbot_history], outputs=[chatbot, user_input])

    # Custom CSS for styling (using HTML component)
    gr.HTML("""
        <style>
            #title {
                text-align: center;  /* Center the title */
                background-color: #6495ED;  /* Green background color */
                color: white;  /* White text */
                padding: 20px;  /* Add padding around the title */
                font-size: 32px;  /* Larger font size */
                border-radius: 10px;  /* Optional: Rounded corners */
            }
            #custom-chart {
            height: 450px !important;  /* Adjust height as needed */
            }
            #chatbot-container {
                background-color: #7FFFD4;
                border-top-left-radius: 10px;
                padding: 10px;
                box-shadow: -2px -2px 10px rgba(0, 0, 0, 0.1);
                overflow-y: auto;
            }
        </style>
    """)


if __name__=="__main__":
    # Launch the app
    demo.launch()