"""
    Scrape data from 'https://cool-proxy.net' into a csv file
"""

# Imports
import requests_html
from bs4 import BeautifulSoup as bs
import json
import csv


URL = "https://cool-proxy.net"


def scrape(soup: bs, tag: str, tag_class=None):
    """
    returns a list scraped tags

    params:
        soup : BeautifulSoup object containing html site data
        tag : HTML tag
        tag_class : Optional class used on tags
    """

    return soup.find_all(tag, class_=tag_class)


def get_headings(soup: bs, exclude=[]):
    """
    returns a list of table headings, which will be used as column names in CSV file

    params:
        soup : BeautifulSoup object containing html site data
        exclude : Optional list of headings to exclude from the output list
    """

    table_headers = scrape(soup, "th", "tHeader")
    headings = [t.text for t in table_headers if t.text not in exclude]
    return headings


def extract_values(proxy_row):
    """
    returns list of values extracted from the proxy row
    """

    children = proxy_row.findChildren()
    values = []
    valid_img_classes = {"ng-scope"}

    for child in children:
        if child.name == "td":
            if not child.text.strip():
                continue
            values.append(child.text.strip())

        elif child.name == "img":
            attrs = child.attrs
            if set(attrs.get("class")) != valid_img_classes:
                continue
            alt = attrs.get("alt")
            if not alt:
                continue
            rating = str(alt)[0]
            values.append(rating)

    return values


def write_to_csv(headings: list, values: list, filename="scrape.csv"):
    print(f"[+] Writing output to {filename}")
    with open(filename, "w") as file:
        writer = csv.writer(file)
        writer.writerow(headings)
        writer.writerows(values)


def main():
    """
    Runner function
    """

    session = requests_html.HTMLSession()
    count = 0
    print(f"[+] Fetching site HTML for URL: {URL}")

    while count < 3:
        response = session.get(URL, timeout=30)
        print(f"[+] Response status code: {response.status_code}")
        if response.status_code == 200:
            break
        print(f"[+] Retrying... ({count+1})")
        count += 1

    print(f"[+] Rendering site HTML. This might take some time...")
    # Rendering is essential as response currently contains exact data returned by server.
    # Rendering resolves the JS into HTML
    response.html.render()
    print(f"[+] HTML rendered successfully")
    html = response.html.html
    soup = bs(html, "html.parser")

    print(f"[+] Fetching table headings")
    headings = get_headings(soup, exclude=["Flag"])
    if not headings:
        print(f"[X] No table headings found. Quitting...")
        exit(0)

    print(f"[+] Fetching table rows")
    proxy_data_rows = scrape(soup, tag="tr", tag_class="proxy-row")
    proxy_values = []

    print(f"[+] Extracting values from fetched table rows")
    for row in proxy_data_rows:
        values = extract_values(row)
        if len(values) != len(headings):
            print(f"[X] Values do not match the table table headings. Quitting...")
            exit(0)

        proxy_values.append(values)

    write_to_csv(headings, proxy_values)
    print(f"[+] Done...")


if __name__ == "__main__":
    main()
