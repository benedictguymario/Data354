# importation des bibliotheques
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
from selenium.webdriver.chrome.options import Options
# Configurer les options du navigateur
op = Options()
op.add_argument("--disable-extensions")
op.add_argument("--disable-gpu")
op.add_argument("--no-sandbox")
op.add_argument("--disable-dev-shm-usage")
op.add_argument("--window-size=1920,1080")
op.add_argument("--start-maximized")
op.add_argument("--disable-infobars")
op.add_argument("--disable-notifications")
op.add_argument("--disable-popup-blocking")
op.add_argument("--disable-default-apps")
op.add_argument("--disable-web-security")
op.add_argument("--disable-logging")
op.add_argument("--log-level=3")
op.add_argument("--silent")

# Augmenter le délai d'attente global
op.page_load_strategy = 'normal'

def scrapper(date_debut, date_fin):
    """
    Cette fonction prend en entrée la date de début et de fin pour scraper les articles correspondants.
    Elle retourne une liste de dictionnaires contenant les titres et les textes des articles.
    """
    # Configuration des options du navigateur
    op = webdriver.ChromeOptions()
    op.page_load_strategy = 'normal'  # Augmenter le délai d'attente global
    driver = webdriver.Chrome(options=op)  # Navigateur principal

    # URL du site à scraper
    url = 'https://www.agenceecofin.com/a-la-une/recherche-article?filterTitle=&submit.x=0&submit.y=0&filterTousLesFils=Tous&filterCategories=Sous-rubrique&filterDateFrom=&filterDateTo=&option=com_dmk2articlesfilter&view=articles&filterFrench=French&Itemid=269&userSearch=1&layout=#dmk2articlesfilter_results'
    driver.get(url)

    # Entrer les dates sélectionnées
    driver.execute_script(f"arguments[0].value = '{date_debut}';", driver.find_elements(By.CLASS_NAME, 'shadow.hasDatepicker')[0])
    driver.execute_script(f"arguments[0].value = '{date_fin}';", driver.find_elements(By.CLASS_NAME, 'shadow.hasDatepicker')[1])

    # Valider l'intervalle de dates
    submit_button = driver.find_element(By.CSS_SELECTOR, "input[name='submit']")
    submit_button.click()

    # Attendre que les résultats soient chargés
    time.sleep(5)  

    # Liste pour stocker les articles
    articles_list = []

    # Boucle pour parcourir toutes les pages
    while True:
        # Récupérer les articles de la page actuelle
        articles = driver.find_elements(By.CLASS_NAME, 'ts')

        # Parcourir chaque article
        for article in articles:
            try:
                # Récupérer l'URL de l'article
                url_art = article.find_element(By.CSS_SELECTOR, 'h3>a').get_attribute('href')

                # Ouvrir l'article dans un nouvel onglet
                driver.execute_script("window.open('');")  
                driver.switch_to.window(driver.window_handles[1])  

                # Charger l'article avec gestion des timeouts
                try:
                    driver.get(url_art)
                except TimeoutException:
                    print(f"Timeout lors du chargement de {url_art}. Réessayer...")
                    driver.refresh()  

                # Récupérer le titre de l'article
                titre = driver.find_element(By.CSS_SELECTOR, 'div>h1').text

                # Récupérer les paragraphes de l'article
                corps = driver.find_elements(By.CLASS_NAME, 'texte.textearticle')
                texte = [para.text for para in corps]

                # Stocker l'article dans un dictionnaire
                article_dict = {
                    'titre': titre,
                    'texte': texte,
                    'url': url_art
                }
                articles_list.append(article_dict)

                # Fermer l'onglet de l'article et revenir à la page principale
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

            except NoSuchElementException as e:
                print(f"Erreur lors du scraping d'un article : {e}")
                continue

        # Passer à la page suivante
        try:
            # Attendre que le bouton "Suivant" soit cliquable
            next_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[title='Suivant']"))
            )
            # Faire défiler la page jusqu'au bouton "Suivant"
            driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)  

            # Cliquer sur le bouton "Suivant" via JavaScript
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(5)  
        except (NoSuchElementException, TimeoutException):
            print("Fin des pages.")
            break

    # Fermer le navigateur principal
    driver.quit()

    return articles_list