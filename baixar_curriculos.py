from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
import time

EMAIL = 'guoliveiradealmeida@gmail.com'
SENHA = 'gugu2004'
URL_VAGA = 'https://www.linkedin.com/hiring/jobs/4019562950/applicants/20218174734/detail/?r=UNRATED%2CGOOD_FIT%2CMAYBE'

options = Options()
options.add_experimental_option("prefs", {
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

def login():
    driver.get("https://www.linkedin.com/login")
    wait.until(ec.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
    driver.find_element(By.ID, "password").send_keys(SENHA)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    print("Login efetuado com sucesso.")
    time.sleep(3)

def scroll_candidate_list():
    container = wait.until(ec.presence_of_element_located(
        (By.CSS_SELECTOR, "div.hiring-applicants__list-container")
    ))
    last_height = driver.execute_script("return arguments[0].scrollHeight;", container)
    while True:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", container)
        time.sleep(1.0)
        new_height = driver.execute_script("return arguments[0].scrollHeight;", container)
        if new_height == last_height:
            break
        last_height = new_height

def remove_interfering_overlays():
    overlays = driver.find_elements(By.CSS_SELECTOR, "div.msg-overlay-bubble-header__details")
    for o in overlays:
        driver.execute_script("arguments[0].style.display='none';", o)

def process_current_page():
    candidates = driver.find_elements(By.CSS_SELECTOR, "li.hiring-applicants__list-item")
    total = len(candidates)
    print(f" → {total} candidatos nesta página.")
    for idx in range(total):
        candidates = driver.find_elements(By.CSS_SELECTOR, "li.hiring-applicants__list-item")
        cand = candidates[idx]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cand)
        time.sleep(0.5)
        cand.click()
        print(f"   [{idx+1}/{total}] Perfil aberto.")
        time.sleep(1.0)

        try:
            nome = wait.until(ec.presence_of_element_located(
                (By.CSS_SELECTOR, "div.artdeco-entity-lockup__content h1")
            )).text.strip()
        except (TimeoutException, NoSuchElementException):
            nome = f"Candidato_{idx+1}"
        print(f"     Processando: {nome}")

        attempts = 0
        success = False
        while attempts < 3 and not success:
            try:
                if driver.find_elements(By.CSS_SELECTOR, "div.hiring-resume-viewer__virus-scan-section"):
                    attempts += 1
                    print(f"       Virus scan detectado → refresh (tentativa {attempts})")
                    driver.refresh()
                    time.sleep(2)
                    continue

                btn = wait.until(ec.element_to_be_clickable((
                    By.XPATH, "//a[contains(@href, '/application/resume/download') or contains(., 'Baixar')]"
                )))
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    print("       Click interceptado → removendo overlays e clicando via JS")
                    remove_interfering_overlays()
                    driver.execute_script("arguments[0].click();", btn)
                print(f"       Download iniciado para {nome}.")
                success = True
                time.sleep(1.5)
            except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                attempts += 1
                print(f"       Erro no download ({attempts}/3): {e}")
                remove_interfering_overlays()
                driver.refresh()
                time.sleep(2)

        if not success:
            print(f"      Falhou após 3 tentativas: {nome}")

def go_to_next_page():
    try:
        next_btn = wait.until(ec.element_to_be_clickable((
            By.CSS_SELECTOR,
            "li.artdeco-pagination__indicator.selected + li button"
        )))
    except TimeoutException:
        return False

    for attempt in range(1, 4):
        try:
            next_btn.click()
            print(" → Avançando para próxima página.")
            time.sleep(2.5)
            return True
        except ElementClickInterceptedException:
            print(f"   Próxima página: click interceptado (tentativa {attempt}/3), removendo overlays")
            remove_interfering_overlays()
            time.sleep(1)
    return False

def main():
    try:
        login()
        driver.get(URL_VAGA)
        time.sleep(3)

        page = 1
        while True:
            print(f"\n=== Página {page} ===")
            scroll_candidate_list()
            process_current_page()
            if not go_to_next_page():
                print("≻ Não há mais páginas. Finalizando.")
                break
            page += 1

    finally:
        print("\nProcesso concluído. Encerrando navegador.")
        driver.quit()

if __name__ == "__main__":
    main()