from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    NoSuchWindowException
)
import time

EMAIL = 'guoliveiradealmeida@gmail.com'
SENHA = 'gugu2004'
URL_VAGA = 'https://www.linkedin.com/hiring/jobs/4018474646/applicants/'

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
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(EMAIL)
    driver.find_element(By.ID, "password").send_keys(SENHA)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    print("Login efetuado com sucesso.")
    time.sleep(3)

def scroll_candidate_list():

    print("Realizando scroll na lista de candidatos...")
    try:
        container = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.hiring-applicants__list-container")
        ))
    except Exception as e:
        print("Não foi possível localizar o container de candidatos.", e)
        return
    last_height = driver.execute_script("return arguments[0].scrollHeight;", container)
    while True:
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", container)
        time.sleep(2)
        new_height = driver.execute_script("return arguments[0].scrollHeight;", container)
        if new_height == last_height:
            break
        last_height = new_height
    print("Scroll finalizado.")

def remove_interfering_overlays():

    overlays = driver.find_elements(By.CSS_SELECTOR, "div.msg-overlay-bubble-header__details")
    if overlays:
        for overlay in overlays:
            driver.execute_script("arguments[0].style.display='none';", overlay)
        print("Overlay(s) removido(s).")
    else:
        pass

def process_candidates():

    candidates = driver.find_elements(By.CSS_SELECTOR, "li.hiring-applicants__list-item")
    total = len(candidates)
    print(f"Foram encontrados {total} candidatos na lista.")

    for i in range(total):
        try:

            candidates = driver.find_elements(By.CSS_SELECTOR, "li.hiring-applicants__list-item")
            if i >= len(candidates):
                print("Número de candidatos alterado; finalizando processamento.")
                break
            candidate = candidates[i]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", candidate)
            time.sleep(1)
            candidate.click()
            print(f"[{i+1}/{total}] Perfil aberto.")
            time.sleep(2)

            try:
                nome_elem = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.artdeco-entity-lockup__content h1")
                ))
                nome_candidato = nome_elem.text.strip()
            except Exception:
                nome_candidato = f"Candidato_{i+1}"
            print(f"Processando: {nome_candidato}")

            attempts = 0
            download_sucesso = False
            while attempts < 3 and not download_sucesso:
                try:

                    virus_scan = driver.find_elements(By.CSS_SELECTOR, "div.hiring-resume-viewer__virus-scan-section")
                    if virus_scan:
                        attempts += 1
                        print(f"Verificação de vírus detectada em {nome_candidato}. Refresh (tentativa {attempts}).")
                        driver.refresh()
                        time.sleep(3)
                        continue

                    download_btn = wait.until(EC.element_to_be_clickable((
                        By.XPATH,
                        "//a[contains(@href, '/application/resume/download') or contains(., 'Baixar')]"
                    )))
                    try:
                        download_btn.click()
                    except ElementClickInterceptedException:
                        print(f"Click interceptado em {nome_candidato}; tentando remover sobreposição.")
                        remove_interfering_overlays()

                        driver.execute_script("arguments[0].click();", download_btn)
                    print(f"Download iniciado para {nome_candidato}.")
                    download_sucesso = True
                    time.sleep(2)
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                    attempts += 1
                    print(f"Erro no download para {nome_candidato}: {e} (tentativa {attempts} de 3).")
                    remove_interfering_overlays()
                    driver.refresh()
                    time.sleep(3)
            if not download_sucesso:
                print(f"Não foi possível baixar o currículo de {nome_candidato} após 3 tentativas.")

            try:
                driver.get(URL_VAGA)
                time.sleep(3)
                scroll_candidate_list()
            except NoSuchWindowException:
                print("A janela principal foi fechada. Encerrando processamento.")
                break

        except NoSuchWindowException as nswe:
            print("Erro crítico – janela não encontrada:", nswe)
            break
        except Exception as e:
            print(f"Erro ao processar candidato {i+1}: {e}")
            try:
                driver.get(URL_VAGA)
                time.sleep(3)
                scroll_candidate_list()
            except NoSuchWindowException:
                print("A janela principal foi fechada. Encerrando processamento.")
                break

def main():
    try:
        login()
        driver.get(URL_VAGA)
        time.sleep(5)
        scroll_candidate_list()
        process_candidates()
    except Exception as e:
        print("Erro no fluxo principal:", e)
    finally:
        print("Processo concluído. Encerrando o navegador.")
        driver.quit()

if __name__ == "__main__":
    main()
