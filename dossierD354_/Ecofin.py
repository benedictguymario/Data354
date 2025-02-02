#CHARGEMENT DES BIBLIOTHEQUES
from typing import List, Dict
import chainlit as cl
from langchain.vectorstores import Chroma
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Chargement  les variables d'environnement
load_dotenv()


# Configuration de l'API GenAI
API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=API_KEY)

# Modèle d'embedding
class SentenceTransformerEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_tensor=True).tolist()

    def embed_question(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_tensor=True).tolist()

# Création du prompt avec historique
def Creat_prompt(question: str, reponse: str, historique: List[Dict[str, str]]) -> str:
    #  l'historique de la conversation
    historique_str = "\n".join([f"Utilisateur : {h['question']}\nAssistant : {h['response']}" for h in historique])
    

    prompt=f"""
        Vous êtes un assistant expert chargé de répondre aux questions des utilisateurs de manière claire, détaillée et précise. Voici les instructions à suivre :
        0. **salutation**: répond aux salutations simplement
        1. **Langue**: Si la question est autre que le français Répondez toujours dans la même langue que la question de l'utilisateur.
        2. **Contexte**: Utilisez les éléments de contexte suivants pour répondre à la question de l'utilisateur. Si le contexte est insuffisant, indiquez-le clairement et fournissez une réponse générale ou suggérez des pistes de réflexion.
        3. **Historique**: Voici l'historique de la conversation :
           {historique_str}
        4. **Format**: pour une meilleure lisibilité. Utilisez des titres, des listes et des mises en forme pour structurer la réponse.
        5. **Détails**: Si la réponse est générale ou incertaine, signalez-le clairement. Si la question est vague ou trop large, demandez des précisions à l'utilisateur.
        6. **Suggestions**: Si la réponse est insuffisante ou absente, suggérez à l'utilisateur des questions liées, comme :
           - « Souhaitez-vous en savoir plus sur un autre sujet ? »
           - « Peut-être pouvez-vous poser une question plus précise sur ce sujet ? »
           - « Si vous avez des questions sur un autre sujet, n'hésitez pas à les poser. »
        7. **Développement**: Si la réponse de l'utilisateur est une affirmation, développez davantage la réponse en fournissant plus de détails.
        8. **Questions courtes**: Si la question est un seul mot, demandez à l'utilisateur s'il souhaite des informations générales ou une réponse précise. Dans ce cas, ne retournez pas de « source ».
        9. **Emojis**: Ajoutez des emojis pour rendre la réponse plus engageante et amicale.

        ---

        **Contexte**: {reponse}

        **Question**: {question}

        ---

        **Réponse utile**:
        """
    return prompt

# Chargement de la base de données
def Obtenir_db(chroma_db_path: str, fonc_embed: SentenceTransformerEmbeddings):
    try:
        db = Chroma(persist_directory=chroma_db_path, embedding_function=fonc_embed)
    except Exception as e:
        return None, f"Erreur : Impossible d'accéder à la collection. Détail : {str(e)}"
    return db, None

# Recherche de contexte dans la base
def Obtenir_contexte(db, question: str, fonc_embed: SentenceTransformerEmbeddings, k: int = 3) -> str:
    try:
        question_embedding = fonc_embed.embed_question(question)
        results = db.similarity_search_by_vector(question_embedding, k=k)
        if not results:
            return "Aucun contexte trouvé."
        docs = [result.page_content for result in results]
        contexte = "\n\n".join(docs)  # Combiner plusieurs articles
    except Exception as e:
        return f"Erreur lors de la récupération du contexte : {str(e)}"
    return contexte

# Génération de réponse
def Reponse(chatbot, prompt: str,model: str) -> str:
    try:
        if model == "gemini-2.0-flash-thinking-exp":
            # Ajouter la partie raisonnement
            thinking_prompt = f"""
            **Démarche de réflexion :**
            Avant de répondre, veuillez analyser et expliquer chaque étape de votre raisonnement pour cette question.
            Ensuite, fournissez la réponse détaillée.

            **Question :** {prompt}
            """
            response = chatbot.generate_content(thinking_prompt)  # Générer une réponse en mode raisonnement
            final_response = response.text # Récupérer la réponse générée
        else:
            # Utiliser le mode normal pour les autres modèles
            response = chatbot.generate_content(prompt)
            final_response = response.text
    except Exception as e:
        return f"Erreur lors de la génération de la réponse : {str(e)}"
    return final_response

# Gestionnaire d'événements Chainlit
@cl.on_chat_start
async def chat_start():
    # Charger le modèle d'embedding et la base de données une seule fois
    fonc_embed = SentenceTransformerEmbeddings()
    db, error = Obtenir_db("Chromadb", fonc_embed)
    if error:
        await cl.Message(content=f"Erreur lors du chargement de la base de données : {error}").send()
        return
    cl.user_session.set("db", db)
    cl.user_session.set("fonc_embed", fonc_embed)
    cl.user_session.set("historique", [])  # Initialiser l'historique de la conversation
    await cl.Message(
        "👋 Bienvenue ! Je suis Ecofin, votre assistant spécialisé pour les articles d'Ecofine.\n"
        "💡 Vous pouvez activer le mode raisonnement pour des analyses plus approfondies.\n"
        "De quel sujet souhaitez-vous discuter ?" 
        ).send()

@cl.set_chat_profiles
# fenetre de choix des model
async def chat_profile():
    return [
        cl.ChatProfile(
            name="gemini-2.0-flash-exp",
            markdown_description="💨 Le modèle **gemini-2.0-flash-exp**.",
            icon="https://picsum.photos/200",
        ),
        cl.ChatProfile(
            name="gemini-2.0-flash-thinking-exp",
            markdown_description="🤔 Mode raisonnement.",
            icon="https://picsum.photos/250",
        ),
        cl.ChatProfile(
            name="gemini-1.5-flash",
            markdown_description="⚡ Le modèle **gemini-1.5-flash**.",
            icon="https://picsum.photos/300",
        ),
    ]

@cl.on_message
async def on_message(message: cl.Message):
    db = cl.user_session.get("db")
    fonc_embed = cl.user_session.get("fonc_embed")
    historique = cl.user_session.get("historique")  # Récupération l'historique de la conversation
    if not db or not fonc_embed:
        await cl.Message(content="Erreur : Base de données non disponible.").send()
        return

    question = message.content
    contexte = Obtenir_contexte(db, question, fonc_embed, k=3)  # Récupérer 3 articles pertinents
    prompt = Creat_prompt(question, contexte, historique)  # Inclusion de l'historique dans le prompt
    model = cl.user_session.get("chat_profile")
    response = Reponse(genai.GenerativeModel(model), prompt,model)
    await cl.Message(content=response).send()

    # Mise à jour l'historique de la conversation
    historique.append({"question": question, "response": response})
    cl.user_session.set("historique", historique)

    # Demander si l'utilisateur est satisfait
    res = await cl.AskActionMessage(
        content="Etes vous satisfait de la reponse ?",
        actions=[
            cl.Action(name="Merci pour votre remarque", payload={"value": "continue"}, label="👍OUI"),
            cl.Action(name="Desole prochainement je essayer de faire mieux", payload={"value": "cancel"}, label="👎 NON"),
        ],
    ).send()

    if res and res.get("payload").get("value") == "continue":
        await cl.Message(
            content="Merci pour votre remarque😊",
        ).send()
    else:
        await cl.Message(
            content="Desole prochainement je essayer de faire mieux 🙏 ",
        ).send()

if __name__ == "__main__":
    cl.run()
   