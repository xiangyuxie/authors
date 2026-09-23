import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates


# dict containing corrections of the first name to avoid having the middle name influencing the order
first_name_fix = {'Kirsty Anne Paton': 'Kirsty Anne'}


def fetch_from_psi():
    # dict containing the name we need to replace with
    # shorter or slightly different variants
    to_fix = {'Lars Erik Fröjd': 'Erik Fröjdh',
              'Maria del Mar Carulla Areste': 'Maria Carulla',
              'Julian Brice Dominique Heymes': 'Julian Heymes',
              'Carlos Lopez Cuenca': 'Carlos Lopez-Cuenca', 
              'Khalil Daniel Ferjaoui': 'Khalil Ferjaoui', 
              'Coline Anne-Marie Francine Vascart': 'Coline Vascart',
              'Alice Francesca Mazzoleni': 'Alice Mazzoleni',
              'Jonathan Franklin Mulvey': 'Jonathan Mulvey',}

    url = 'https://www.psi.ch/en/lxn/team'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    id_tags = ['article__content',]
    names = []
    for id_tag in id_tags:
        results = soup.find(class_=id_tag)
        # print(results)
        # groups = results.find_all("div", class_='psi-summary-media-wrapper')
        "psi-people-reference__name"
        groups = results.find_all("div", class_="psi-people-reference__name")  
        # print(groups)
        # return groups
        for item in groups:
    #         res = item.find("strong", class_="content-item__title heading")
            name = item.text.strip('\n')
            name = name.replace('Dr. ', '')
            if name in to_fix:
                name = to_fix[name]
            names.append(name)

    names = list(set(names))  # remove duplicates
    names.sort(key=lambda s: s.split(maxsplit=1)[1].casefold())

    return names


def tex_jinst(names):
    # assume that the first author is corresponding author
    names = [tex_replace_umlaut(name) for name in names]
    names_iter = iter(names)

    first = f'\\author[a,1]{{{next(names_iter).replace(" ", "~")},\\note{{Corresponding author.}}}} '
    *names_iter, last_author = names_iter
    rest = ' '.join(f'\\author[a]{{{name.replace(" ", "~")},}}' for name in names_iter)
    last = f' \\author[a,1]{{and~{last_author.replace(" ", "~")}}}'
    return first + rest + last


def tex_replace_umlaut(name):
    name = name.replace('å', '\\aa ')
    name = name.replace('ö', '\\"o')
    name = name.replace('ä', '\\"a')
    name = name.replace('ü', '\\"u')
    return name


def get_names(lastname=None):
    result = {}
    names = fetch_from_psi()
    # Reorder with the first name correction
    all_lastnames = []
    for name in names:
        if name in first_name_fix:
            ln = name.replace(f"{first_name_fix[name]} ", '')
        else:
            _, ln = name.split(maxsplit=1)
        all_lastnames.append(ln)
    all_lastnames, names = zip(*sorted(zip(all_lastnames, names)))
    names = list(names)

    if lastname:
        lastname = lastname.casefold()
        for i, name in enumerate(names):
            if lastname in name.partition(' ')[2].casefold():
                names.insert(0, names.pop(i))
                break

    result['full'] = ', '.join(names)
    result['n_members'] = len(names)
    # print(names)

    short = []
    for name in names:
        if name in first_name_fix:
            first = first_name_fix[name]
            last = name.replace(f"{first} ", '')
        else:
            first, last = name.split(maxsplit=1)
        initials = ".".join([firstname[0] for firstname in first.split(" ")])
        short.append(name.replace(first, f"{initials}."))

    result['short'] = ', '.join(short)

    result['jinst_full'] = tex_jinst(names)
    result['jinst_short'] = tex_jinst(short)

    return result


templates = Jinja2Templates(directory="templates/")
app = FastAPI()


@app.get("/")
async def read_root(request: Request):
    result = get_names()
    return templates.TemplateResponse("main.html", context={"request": request, "result": result})


@app.get("/author/{lastname}")
async def read_author(request: Request, lastname):
    result = get_names(lastname)
    return templates.TemplateResponse("main.html", context={"request": request, "result": result})

if __name__ == "__main__":
    res = get_names()
    print()
    for key, value in res.items():
        print(f"{key}:\n {value}\n")