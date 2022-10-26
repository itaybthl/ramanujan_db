import itertools
import datetime
import requests
from bs4 import BeautifulSoup
import json
import time
import sympy
from PCF import PCF
from insert_pcf_into_db import add_multiple_pcfs

FILE_PATH_INDEX = 1
FILE_DATE_INDEX = 2

def get_url_paths(url, params={}, file_start_date="1970-01-01"):
    """
    url: The url of the boinc path of the list of files.
    Return a list of urls of all the files in boinc created after {earliest_file_time}
    """
    response = requests.get(url, params=params)
    if response.ok:
        response_text = response.text
    else:
        return response.raise_for_status()
    soup = BeautifulSoup(response_text, 'html.parser')

    files_list = []
    if type(file_start_date) is type("string"):
        file_start_date = datetime.datetime.strptime(file_start_date, "%Y-%m-%d")
    tr_list = soup.find_all("tr") # This is a list of all of the rows in the page
    for tr in tr_list:
        # if tr.find("a") is not None and tr.find("a").get("href") is not None \
        #     and "RNM" in tr.find("a").get("href"):

        td_list = tr.find_all("td") # These are the elements in each row
        if len(td_list) >= 4 and "RNM" in td_list[FILE_PATH_INDEX].text:
            file_time = datetime.datetime.strptime(td_list[FILE_DATE_INDEX].text, "%Y-%m-%d %H:%M ")
            if file_time > file_start_date:
                files_list.append(url + td_list[FILE_PATH_INDEX].text)
    # parent = [url + node.get('href') for node in soup.find_all('a') if "RNM" in node.get('href')]
    return files_list


def get_data_from_boinc(file_start_date):
    url = 'https://rnma.xyz/boinc/result/'
    file_names = get_url_paths(url, file_start_date=file_start_date)
    results = {}

    for name in file_names:
        if ".png" in name:
            continue
        response = requests.get(name, {})
        if response.ok:
            response_text = response.text
        else:
            response.raise_for_status()
        results[name.split("/")[-1]] = json.loads(response_text)
        print(name.split("/")[-1])

    return results


def load_data_from_file(path):
    with open(path, "r") as f:
        results = json.load(f)
    return results


def translate_zeta_5_scheme(results):
    n = sympy.Symbol("n")
    for result in results.keys():
        if result.startswith("RNM_zeta5") and not result.startswith("RNM_zeta5_doms"):
            an_coefs = results[result][0][0]
            bn_coefs = results[result][0][1]
            new_an = sympy.Poly(an_coefs[0] * (n**5 + (n+1)**5) + an_coefs[1] * (n**3 + (n+1)**3) + an_coefs[2] * (2*n + 1))
            new_bn = sympy.Poly(-1 * (bn_coefs[0]**2) * n**10)
            results[result] = [[[int(i) for i in new_an.all_coeffs()], [int(j) for j in new_bn.all_coeffs()]]]
    return results


def get_simple_results(results):
    """
    Translate from the format of boinc to a list of lists:[[an_coefs, bn_coefs],...]
    Remember to have the largest power on the left.
    """
    # Not very pretty, this flattens the list of lists into a single list of all of the PCFs.
    _simple_results = [result for sublist in [results[key] for key in results.keys()] for result in sublist]
    simple_results = [(result[0], result[1]) for result in _simple_results]
    return simple_results


def print_pcf_groups(a):
    for i in range(len(a)):
        if len(a[i][1]) != 1:
            print("Line: " + str(i))
            print(a[i][0])
            for j in a[i][1]:
                print(j)


def group_similar_pcfs(pcfs):
    """
    Receive list(PCF), print each group together.
    """
    canonical_pcfs = [(pcf, pcf.get_cannonical_form_string(), pcf.get_cannonical_form()) for pcf in pcfs]
    canonical_pcfs.sort(key=lambda x: x[1])
    a = [(k, [v[0] for v in list(g)]) for k, g in
         itertools.groupby(sorted(canonical_pcfs, key=lambda x: x[1]), lambda x: x[1])]

    print_pcf_groups(a)


def main():
    a_week_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    results = get_data_from_boinc(file_start_date=a_week_ago)
    # results = load_data_from_file(r"C:\Ramanujan\ramanujan_results\1662298882.131278.json")
    results = translate_zeta_5_scheme(results)

    simple_results = get_simple_results(results)
    # simple_results = get_test_data()

    pcfs = [PCF(result[0], result[1]) for result in simple_results]
    # group_similar_pcfs(pcfs)
    # This is to make sure the printing ends before exceptions might be thrown from the db functions.
    time.sleep(0.1)

    success, failure = add_multiple_pcfs(pcfs)
    print("Added:")
    print("\n".join([str(s) for s in success]))
    print("Already exist:")
    print("\n".join([str(f) for f in failure["Already exist"]]))
    print("No FR:")
    print("\n".join([str(f) for f in failure["No FR"]]))
    print("END")
    # with open("C:\\Ramanujan\\ramanujan_results\\" + str(time.time()) + ".json", "w") as f:
    #     json.dump(results, f)



if __name__ == "__main__":
    main()
