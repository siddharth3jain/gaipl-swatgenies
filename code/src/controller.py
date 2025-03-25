import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from registered_files import llm_model, embeddings_model, client, df_incidents, df_configuration_data, df_recommendations, df_kb_articles, df_incidents_embed


def llm_response(input_text, chatbot_activation=False):
    if chatbot_activation is True:
        chat_response = client.chat.complete(model=llm_model, messages=input_text)
        return chat_response.choices[0].message.content
    else:
        chat_response = client.chat.complete(
            model=llm_model,
            messages=[
                {
                    "role": "user",
                    "content": input_text,
                },
            ]
        )
        return chat_response.choices[0].message.content


def create_embeddings(input_texts:list):
    embeddings_batch_response = client.embeddings.create(
        model=embeddings_model,
        inputs=input_texts,
    )
    return [item.embedding for item in embeddings_batch_response.data]


def save_incidence_embeddings():
    embeddings_incidence = create_embeddings(df_incidents['description'].tolist())
    incidence_desc_emb_df = pd.DataFrame(embeddings_incidence,index=df_incidents['incident_id'])
    incidence_desc_emb_df.to_pickle(r'./data/incidence_desc_emb_df_new.pkl')
    print("Embeddings Saved")

def get_nearest_match(user_input, top_n=50):
    user_input = [user_input.strip().lower()]
    user_emb = create_embeddings(user_input)
    sim = cosine_similarity(np.array(user_emb[0]).reshape(1, -1), np.array(df_incidents_embed.values)).flatten()
    top_n_indices = np.argsort(sim)[::-1][:top_n]
    top_n_df = df_incidents_embed.iloc[top_n_indices]
    top_n_df.loc[:,'similarity_score'] = sim[top_n_indices]
    starting_sim_score = 1
    while True:
        starting_sim_score -= 0.1
        top_n_df_temp = top_n_df[top_n_df['similarity_score']>starting_sim_score]
        if len(top_n_df_temp)>0 or starting_sim_score == 0.6:
            break
    return top_n_df_temp.index.tolist()


# Function to create graphs

# Function to display relevant incidence and telemetry data
def create_master_data(input_text:str):
    ## get the required details about the top incidence matches
    top_matches = get_nearest_match(input_text,top_n=50)
    df_incident_filtered = df_incidents[df_incidents['incident_id'].isin(top_matches)]

    # Define custom order
    custom_order = ['Open', 'In Progress', 'Resolved', 'Closed']
    # Convert column to categorical with specified order
    df_incident_filtered['Category'] = pd.Categorical(df_incident_filtered['status'], categories=custom_order, ordered=True)
    # Sort DataFrame
    df_incident_filtered = df_incident_filtered.sort_values(by='Category')

    df_incident_display = df_incident_filtered[['incident_id','description','status','source','created_at','resolved_at']]
    df_telemetry_display = df_incident_filtered[['incident_id','cpu_usage', 'memory_usage', 'disk_io_latency', 'network_latency']]
    return df_incident_display, df_telemetry_display


if __name__=="__main__":
    save_incidence_embeddings()