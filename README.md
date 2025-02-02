# **📚 Documentation de la solution : Chatbot Ecofin 🤖**

## Structure du dossier Dossier354_

- **D54 (Scrapper)** : Fonction qui prend en paramètre la date de début (`AAAA-MM-JJ`) et la date de fin (`AAAA-MM-JJ`).
- **Ecofin** : Fichier contenant le code source du chatbot.
- **ChromaDB** : Base de données vectorielle qui constitue la base de connaissance.
- **requirement.txt** : Fichier contenant les dépendances nécessaires au bon fonctionnement du chatbot.


## **🔍 Introduction**

Ce code implémente un chatbot intelligent utilisant **Chainlit** et l'API **Google Generative AI (GenAI)**, combiné à un moteur d'**embedding** basé sur **Sentence-Transformers** pour la recherche de contenu pertinent dans une base de données **Chroma**. Le chatbot aide les utilisateurs à obtenir des informations détaillées sur des articles du site *Ecofin*.

---

## **🛠 Composants principaux**

1. **Chainlit** 💬 : Utilisé pour la gestion de la conversation, y compris l'authentification, l'historique et l'interaction avec l'utilisateur.
2. **Sentence-Transformers** 🧠 : Utilisé pour transformer les textes en embeddings et permettre des recherches dans la base de données.
3. **Google Generative AI (GenAI)** 🤖 : Utilisé pour générer des réponses aux questions des utilisateurs en fonction du prompt.
4. **Chroma** 💾 : Une base de données vectorielle permettant de stocker et rechercher des documents en fonction de leur similarité.

---

## **🚀 Pré-requis**

Avant de lancer l'application, assurez-vous que vous avez installé toutes les dépendances nécessaires et configuré l'environnement.

### **Dépendances Python** 📦

- `chainlit` : Pour créer et gérer l'interface de conversation.
- `langchain` : Pour gérer la base de données vectorielle Chroma.
- `sentence-transformers` : Pour transformer le texte en embeddings.
- `google-generativeai` : API de génération de texte de Google.
- `python-dotenv` : Pour charger les variables d'environnement à partir d'un fichier `.env`.

Installez ces bibliothèques avec la commande `pip` :

```bash
pip install -r requrement.txt
```

---

### **🔑 Clé API GenAI**

1. Créez un fichier `.env`  dans le répertoire racine de votre projet et ajoutez votre clé API ou (vous pouvez  utiliser la clé qui se trouve dans le fichier`.env` que vous pour le deplacer dans le dossier `Dossier354_`.(lien:https://aistudio.google.com/app/apikey?hl=fr&_gl=1*1p959pl*_ga*MTMyNDkxODU2OS4xNzM3OTE5ODQ2*_ga_P1DBVKWT6V*MTczODUzMDA4Ni4xMS4wLjE3Mzg1MzAwODYuNjAuMC4zMjU3MDM3NA..) comme suit :

```plaintext
GENAI_API_KEY=Cle_api
```

---

## **🧑‍💻 Structure du code**

### 1. **Initialisation et chargement des bibliothèques** 🔌

Le code commence par importer les bibliothèques nécessaires et charger les variables d'environnement.

```python
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")
genai.configure(api_key=API_KEY)
```

### 2. **Classe `SentenceTransformerEmbeddings` 🧠**

Cette classe encode les documents et les questions en embeddings grâce à **Sentence-Transformers**.

```python
class SentenceTransformerEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_tensor=True).tolist()

    def embed_question(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_tensor=True).tolist()
```

### 3. **Chargement de la base de données Chroma 📚**

La fonction `Obtenir_db` charge la base de données Chroma persistée contenant les documents.

```python
def Obtenir_db(chroma_db_path: str, fonc_embed: SentenceTransformerEmbeddings):
    try:
        db = Chroma(persist_directory=chroma_db_path, embedding_function=fonc_embed)
    except Exception as e:
        return None, f"Erreur : Impossible d'accéder à la collection. Détail : {str(e)}"
    return db, None
```

### 4. **Recherche de contexte dans la base de données 🔍**

La fonction `Obtenir_contexte` effectue une recherche dans la base pour récupérer des documents pertinents en fonction de la question de l'utilisateur.

```python
def Obtenir_contexte(db, question: str, fonc_embed: SentenceTransformerEmbeddings, k: int = 3) -> str:
    question_embedding = fonc_embed.embed_question(question)
    results = db.similarity_search_by_vector(question_embedding, k=k)
    if not results:
        return "Aucun contexte trouvé."
    docs = [result.page_content for result in results]
    contexte = "\n\n".join(docs)
    return contexte
```

### 5. **Création du prompt ✍️**

Le prompt généré inclut l'historique de la conversation et le contexte pertinent. Il est envoyé à l'API GenAI pour générer une réponse.

```python
def Creat_prompt(question: str, reponse: str, historique: List[Dict[str, str]]) -> str:
    historique_str = "\n".join([f"Utilisateur : {h['question']}\nAssistant : {h['response']}" for h in historique])
    
    prompt = f"""
    Vous êtes un assistant expert chargé de répondre aux questions des utilisateurs de manière claire, détaillée et précise. Voici les instructions à suivre :
    0. **salutation**:...
    1. **Langue** :...
    ...
    **Contexte** : {reponse}
    **Question** : {question}
    ---
    **Réponse utile** :
    """
    return prompt
```

### 6. **Génération de la réponse 💡**

La fonction `Reponse` interroge l'API GenAI avec le prompt généré et renvoie la réponse.

```python
def Reponse(chatbot, prompt: str) -> str:
    try:
        response = chatbot.generate_content(prompt)
        final_response = response.text
    except Exception as e:
        return f"Erreur lors de la génération de la réponse : {str(e)}"
    return final_response
```

### 7. **Gestionnaire d'événements Chainlit 🎮**

Les gestionnaires d'événements Chainlit définissent le comportement du chatbot, notamment lors du démarrage de la conversation et à la réception des messages. L'historique est mis à jour et une enquête de satisfaction est envoyée à l'utilisateur après chaque réponse.

```python
@cl.on_chat_start
async def chat_start():
    fonc_embed = SentenceTransformerEmbeddings()
    db, error = Obtenir_db("Chromadb", fonc_embed)
    if error:
        await cl.Message(content=f"Erreur lors du chargement de la base de données : {error}").send()
        return
    ...
```

---

## **🚀 Lancer l'application**

1. **Démarrer l'application** : Vous pouvez démarrer le chatbot avec la commande suivante :

```bash
chainlit run  Ecofin.py
```

2. **Interaction avec l'utilisateur** :  L'utilisateur pourra poser des questions et le chatbot répondra en fonction du contenu de la base de données.

3. **Réponses et enquête de satisfaction** : Après chaque réponse, une enquête de satisfaction est envoyée pour savoir si l'utilisateur est satisfait de la réponse.

---

## **🎨 Personnalisation**

- **Choix du modèle** : Dans la fonction `chat_profile`, vous pouvez définir différents modèles pour le chatbot, permettant à l'utilisateur de choisir entre plusieurs options.
- **Base de données Chroma** : Vous pouvez ajuster le chemin du fichier Chroma et le nombre de documents retournés (via le paramètre `k`).

---

## **🔚 Conclusion**

Ce chatbot utilise une combinaison d'outils puissants pour fournir des réponses intelligentes et pertinentes basées sur des articles du site *Ecofin*. Il gère l'historique des conversations, le contexte pertinent des articles, et fournit des réponses personnalisées tout en recueillant des retours utilisateurs pour améliorer son service.

# Remarque:
### 🔹 **1️⃣ Gemini-1.5-Flash**  
✅ **Points forts** :  
- **Ultra-rapide** et optimisé pour **des tâches simples et courtes**.

### 🔹 **2️⃣ Gemini-1.5-Flash-Exp**  
✅ **Points forts** :  
- Basé sur **Gemini-1.5-Flash**, mais avec une **capacité d'expansion**.  
- Meilleur traitement des **conversations longues** et des **analyses plus détaillées**

### 🔹 **3️⃣ Gemini-2-Thinking-Exp**  
✅ **Points forts** :  
- **Version avancée pour le raisonnement approfondi** et les tâches complexes.  
- Capacité à **analyser, structurer et générer des réponses détaillées**.  
- Idéal pour **les analyses financières, les décisions stratégiques et la compréhension approfondie**.  
- Peut **expliquer son raisonnement** étape par étape. 
