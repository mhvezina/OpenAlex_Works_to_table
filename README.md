# OpenAlex Works JSON → CSV/TSV (multi-lignes)  
### Aplatissement de type export / export-like flattening

**Auteur** : Marie-Hélène Vézina, Bibliothèques, Université de Montréal   
**Licence** : GNU General Public License v3.0   
**Version** : 1.0  
**Description courte (fr)** : Conversion d'un fichier JSON OpenAlex (works) déjà collecté via l'API vers un format tabulaire CSV/TSV reproduisant fidèlement la structure de l'export natif d’OpenAlex.  
**Description courte (en)** : Conversion of an OpenAlex JSON file (works), already collected via the API, into a tabular CSV/TSV format that faithfully reproduces the structure of the native OpenAlex export.


---

_English follows_

## Description

Ce programme tente d'émuler au plus près la sortie CSV de l'interface de recherche d'OpenAlex (fonction `Export`) en partant d'un fichier JSON déjà obtenu via l'API OpenAlex.  
Il **ne contacte pas l’API** et **ne gère pas la pagination** : il prend un seul fichier JSON en entrée, contenant des notices `works` déjà récupérées par un autre processus.

### À propos des entités *dehydrated* (versions allégées)

Dans un objet *Work*, certaines entités imbriquées sont renvoyées en version *dehydrated*.  
Entités concernées : `author`, `institution`, `source`, `concept`, `topic`, `funder`.

---

### Formes d’entrée JSON acceptées (un seul fichier à la fois)

1. **Objet JSON unique** correspondant à *une seule notice* :
   ```json
   {
     "id": "https://openalex.org/W123",
     "title": "Un titre",
     "publication_year": 2025
   }
   ```

2. **Liste JSON** contenant plusieurs objets *work* :
   ```json
   [
     { "id": "https://openalex.org/W1", "title": "A" },
     { "id": "https://openalex.org/W2", "title": "B" }
   ]
   ```

3. **Objet JSON au format API** avec la clé `results` :
   ```json
   {
     "meta": { "count": 2 },
     "results": [
       { "id": "https://openalex.org/W1", "title": "A" },
       { "id": "https://openalex.org/W2", "title": "B" }
     ]
   }
   ```

---

### Sortie

CSV ou TSV (TSV par défaut).  
L'en-tête et l’ordre des colonnes reproduisent un export *usage-like* et incluent diverses normalisations :

- **Champs booléens** : par défaut en anglais (`True`/`False`). Avec `--bool-style fr`, rendus en `Vrai`/`Faux`.
- **Champs `raw*` et titres** (`title`, `display_name`) : nettoyage des retours de ligne et tabulations.
- **Listes** : jointes avec un séparateur (par défaut `|`) en remplaçant les jetons vides par `--list-missing-token` (`None` par défaut).  
  - Liste absente ou vide → `--cell-missing` (vide par défaut).  
  - Liste existante mais entièrement vide → un seul jeton manquant.
- **Champs scalaires vides** → `--cell-missing`.
- **Résumé** : reconstruit depuis `abstract_inverted_index` si présent, sinon `abstract`.

---

### Champs particuliers

#### `authorships.institutions` et `authorships.affiliations`

- Sortie **par auteur**, séparés par `|` (`--list-sep`).  
- À l'intérieur d’un auteur : institutions séparées par `;`.  
- S'il manque une institution, insertion du jeton `--list-missing-token` (`None` par défaut).  
- Formats utilisés avant `;` :
  - **institutions** → `id`, `"display_name"`, `ror`, `country_code`, `type`, `[lineage]`
  - **affiliations** → `"raw_affiliation_string"`, `[institution_ids]`

**Exemple minimal :**
```json
"authorships": [
  {
    "author": { "display_name": "Alice" },
    "institutions": [
      {
        "id": "https://openalex.org/I1",
        "display_name": "Université A",
        "ror": "https://ror.org/01aaaaa11",
        "country_code": "CA",
        "type": "education",
        "lineage": ["https://openalex.org/I1"]
      },
      {
        "id": "https://openalex.org/I2",
        "display_name": "Institut B",
        "ror": "https://ror.org/02bbbbb22",
        "country_code": "FR",
        "type": "nonprofit",
        "lineage": ["https://openalex.org/I2"]
      }
    ]
  },
  {
    "author": { "display_name": "Bob" },
    "institutions": [
      {
        "id": "https://openalex.org/I3",
        "display_name": "Université C",
        "ror": "https://ror.org/03ccccc33",
        "country_code": "US",
        "type": "education",
        "lineage": ["https://openalex.org/I3"]
      }
    ]
  }
]
```

**Résultat dans la cellule :**
```
https://openalex.org/I1, "Université A", https://ror.org/01aaaaa11, CA, education, ['https://openalex.org/I1']; https://openalex.org/I2, "Institut B", https://ror.org/02bbbbb22", FR, nonprofit, ['https://openalex.org/I2']|https://openalex.org/I3, "Université C", https://ror.org/03ccccc33, US, education, ['https://openalex.org/I3']
```

---

#### `datasets` et `versions`

Peuplement rare dans les données OpenAlex.  
Conservent leur structure d’origine pour compatibilité.

---

#### `counts_by_year`

Aplati en deux colonnes synchronisées :  
- `counts_by_year.year`  
- `counts_by_year.cited_by_count`

---

### Journalisation

Un fichier log liste toutes les colonnes produites et le nombre total de lignes écrites.

---

### Utilisation

```bash
# TSV (par défaut)
python openalex_work_to_table.py --json-in works.json -o out.tsv --format tsv     --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.tsv.log

# CSV
python openalex_work_to_table.py --json-in works.json -o out.csv --format csv     --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.csv.log
```

---

## Description (en)

This script closely emulates the CSV export from the OpenAlex search UI, using a JSON file already retrieved from the API.  
It **does not call the API** and **does not handle pagination** — it processes a single JSON file containing `work` records.

### Input formats

1. Single `work` JSON object  
2. JSON array of `work` objects  
3. API-style JSON with a `results` list

### Output

CSV or TSV, reproducing the UI export structure.  
Normalization rules mirror the French section above.

### Special handling

- **`authorships.institutions` and `authorships.affiliations`**  
  Per-author, joined with `|` and `;` separators.  
  Missing elements replaced with `--list-missing-token`.

- **`counts_by_year`** flattened into:
  - `counts_by_year.year`
  - `counts_by_year.cited_by_count`

### Logging

A log file lists all output columns and total rows written.

### Usage

```bash
python openalex_work_to_table.py --json-in works.json -o out.tsv --format tsv     --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.tsv.log
```

---

## Licence

Ce programme est distribué sous les termes de la **GNU General Public Licence v3.0**.  
Vous êtes libre de l'utiliser, de le modifier et de le redistribuer, à condition de conserver la même licence et d'attribuer la paternité à l'auteur original.  
Consultez le fichier de license pour le texte complet.

---


