#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAlex Works JSON → CSV/TSV (multi-lignes) — aplatissement de type export / export-like flattening
===================================================================
Français:
Ce programme tente d'emuler au plus près la sortie CSV de l'interface de recherche
d'OpenAlex (fonction 'Export') en partant d'un fichier JSON déjà obtenu via l'API
OpenAlex. Il ne contacte PAS l'API et ne gère PAS la pagination: il prend un seul
fichier JSON en entrée, contenant des notices 'works' déjà récupérées par un processus autre.

A propos des entités 'dehydrated' (versions allégées):
Dans un objet Work, certaines entités imbriquées sont renvoyées en version 'dehydrated'.
Entités concernées: author, institution, source, concept, topic, funder.

Formes d'entrée JSON acceptées (un seul fichier à la fois) :
1) Un objet JSON unique correspondant à UNE notice 'work'.
   Exemple :
   {
     "id": "https://openalex.org/W123",
     "title": "Un titre",
     "publication_year": 2025
   }

2) Une liste JSON contenant plusieurs objets 'work'.
   Exemple :
   [
     { "id": "https://openalex.org/W1", "title": "A" },
     { "id": "https://openalex.org/W2", "title": "B" }
   ]

3) Un objet JSON au format API avec la clé 'results' dont la valeur est une liste d'objets 'work'.
   Exemple :
   {
     "meta": { "count": 2 },
     "results": [
       { "id": "https://openalex.org/W1", "title": "A" },
       { "id": "https://openalex.org/W2", "title": "B" }
     ]
   }

Sortie:
CSV ou TSV (TSV par défaut). L'en-tête et l'ordre des colonnes reproduisent un export usage-like
et incluent diverses normalisations:
- Champs booléens: par défaut en anglais ('True'/'False', valeur originale). Avec --bool-style fr,
  ils sont rendus en 'Vrai'/'Faux'.
- Champs dont le nom commence par 'raw': nettoyage des retours de ligne et tabulations.
- Titres (title, display_name): nettoyage des retours de ligne et tabulations.
- Listes: jointes avec un séparateur (par défaut '|') en remplaçant tout jeton vide par
  --list-missing-token (défaut: 'None') pour éviter les séquences '||', '|||', ou '|valeur|'.
  Si la liste entière est absente/vide -> cellule vide via --cell-missing.
  Si la liste existe mais que tous les jetons sont manquants -> on renvoie UN SEUL jeton manquant.
- Champs scalaires vides -> --cell-missing (par défaut: chaîne vide).
- L'abstract est reconstruit à partir de 'abstract_inverted_index' si présent, sinon 'abstract'.

Champs particuliers:
- authorships.institutions et authorships.affiliations:
  Sortie par auteur. Les auteurs sont séparés par '|' (ou --list-sep). A l'intérieur d'un auteur,
  toutes les institutions (ou affiliations) sont conservées et séparées par ';'.
  S'il manque une institution/affiliation pour un auteur, le jeton manquant --list-missing-token
  (défaut: 'None') est inséré pour préserver l'alignement avec les autres colonnes authorships.*.
  Formats utilisés (par entrée, avant le ';'):
    institutions -> id, "display_name", ror, country_code, type, [lineage]
    affiliations -> "raw_affiliation_string", [institution_ids]

Exemple d'entrée JSON minimale et de sortie pour la colonne 'authorships.institutions' :
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

Résultat dans la cellule 'authorships.institutions' (avec list-sep='|'):
  https://openalex.org/I1, "Université A", https://ror.org/01aaaaa11, CA, education, ['https://openalex.org/I1']; https://openalex.org/I2, "Institut B", https://ror.org/02bbbbb22", FR, nonprofit, ['https://openalex.org/I2']|https://openalex.org/I3, "Université C", https://ror.org/03ccccc33, US, education, ['https://openalex.org/I3']

- datasets et versions:
  Conservés tels quels et souvent vides, car rarement peuplés et non documentés officiellement.
  Ils restent dans l'en-tête pour compatibilité, sans traitement spécial.

Counts par année:
- 'counts_by_year' est aplati en deux colonnes parallèles synchronisées:
  'counts_by_year.year' et 'counts_by_year.cited_by_count'. Chaque position i correspond
  à la même année i et au même compte i.

Journalisation:
Un fichier log liste toutes les colonnes produites et le nombre total de lignes écrites.

Utilisation:
    # TSV (par défaut)
    python openalex_work_to_table.py --json-in works.json -o out.tsv --format tsv \
        --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.tsv.log

    # CSV
    python openalex_work_to_table.py --json-in works.json -o out.csv --format csv \
        --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.csv.log


ENGLISH:

This script aims to closely emulate the CSV export from the OpenAlex search UI, using a JSON file
already retrieved from the API. It does NOT call the API and does NOT handle pagination: it processes
one input JSON file containing 'work' records obtained by some other process.

About 'dehydrated' entities:
In a Work object, some embedded entities are returned in a dehydrated (lightweight) form.
Entities: author, institution, source, concept, topic, funder.

Accepted JSON input shapes (one file at a time):
1) A single JSON object representing ONE 'work'.
   Example:
   {
     "id": "https://openalex.org/W123",
     "title": "A title",
     "publication_year": 2025
   }

2) A JSON array containing multiple 'work' objects.
   Example:
   [
     { "id": "https://openalex.org/W1", "title": "A" },
     { "id": "https://openalex.org/W2", "title": "B" }
   ]

3) A JSON object in the API shape that has a 'results' key with a list of 'work' objects.
   Example:
   {
     "meta": { "count": 2 },
     "results": [
       { "id": "https://openalex.org/W1", "title": "A" },
       { "id": "https://openalex.org/W2", "title": "B" }
     ]
   }

Output:
CSV or TSV (TSV by default). The header and column order mimic the UI export and apply:
- Booleans default to EN ('True'/'False'); with --bool-style fr they become 'Vrai'/'Faux'.
- 'raw*' fields sanitized (strip newlines/tabs).
- Titles (title, display_name) sanitized (strip newlines/tabs).
- Lists joined with a separator (default '|'), replacing empty inner tokens with --list-missing-token
  (default 'None') to avoid '||', '|||', or '|value|'.
  If the whole list is missing/empty -> use --cell-missing.
  If the list exists but all tokens are missing -> return a SINGLE missing token.
- Missing scalars -> --cell-missing (default: empty).
- Abstract rebuilt from 'abstract_inverted_index' when present, else 'abstract'.

Special fields:
- authorships.institutions and authorships.affiliations:
  Per-author output. Authors are separated by '|' (or --list-sep). Within a single author,
  all institutions (or affiliations) are preserved and separated by ';'.
  If an author has none, the --list-missing-token (default 'None') is inserted to preserve
  alignment across authorships.* columns.
  Formats per entry (before the ';'):
    institutions -> id, "display_name", ror, country_code, type, [lineage]
    affiliations -> "raw_affiliation_string", [institution_ids]

Minimal JSON input and resulting cell for 'authorships.institutions' (two authors,
first author has two institutions; list-sep='|'):
  Input:
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

  Output cell for 'authorships.institutions':
    https://openalex.org/I1, "Université A", https://ror.org/01aaaaa11, CA, education, ['https://openalex.org/I1']; https://openalex.org/I2, "Institut B", https://ror.org/02bbbbb22, FR, nonprofit, ['https://openalex.org/I2']|https://openalex.org/I3, "Université C", https://ror.org/03ccccc33, US, education, ['https://openalex.org/I3']

- datasets and versions:
  Kept as-is and commonly empty, for compatibility.

Counts by year:
- 'counts_by_year' is flattened into two synchronized columns:
  'counts_by_year.year' and 'counts_by_year.cited_by_count'.

Logging:
A log file lists all output columns and the total number of rows written.

Usage:
    # TSV (default)
    python openalex_work_to_table.py --json-in works.json -o out.tsv --format tsv \
        --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.tsv.log

    # CSV
    python openalex_work_to_table.py --json-in works.json -o out.csv --format csv \
        --bool-style en --cell-missing "" --list-missing-token "None" --list-sep "|" --log-out out.csv.log
"""
import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterable

# ==============================
# En-tête figé / Fixed header (exact order)
# ==============================
HEADER_COLS = [
    # Identité / Identity
    "id","doi","title","display_name","publication_year","publication_date","language",
    "type","type_crossref","indexed_in","institution_assertions","countries_distinct_count",
    "institutions_distinct_count","corresponding_author_ids","corresponding_institution_ids",
    "fwci","has_fulltext","fulltext_origin","cited_by_count","is_retracted","is_paratext",
    "locations_count",
    # Données API divers / Misc API data
    "datasets","versions","referenced_works_count","referenced_works","related_works","cited_by_api_url",
    # counts_by_year split
    "counts_by_year.year","counts_by_year.cited_by_count",
    # Dates
    "updated_date","created_date",
    # ids.*
    "ids.openalex","ids.doi","ids.mag","ids.pmid","ids.pmcid",
    # primary_location.*
    "primary_location.is_oa","primary_location.landing_page_url","primary_location.pdf_url",
    "primary_location.source.id","primary_location.source.display_name","primary_location.source.issn_l",
    "primary_location.source.issn","primary_location.source.is_oa","primary_location.source.is_in_doaj",
    "primary_location.source.is_indexed_in_scopus","primary_location.source.is_core",
    "primary_location.source.host_organization","primary_location.source.host_organization_name",
    "primary_location.source.host_organization_lineage","primary_location.source.host_organization_lineage_names",
    "primary_location.source.type","primary_location.license","primary_location.license_id",
    "primary_location.version","primary_location.is_accepted","primary_location.is_published",
    # open_access.*
    "open_access.is_oa","open_access.oa_status","open_access.oa_url","open_access.any_repository_has_fulltext",
    # APCs
    "apc_list.value","apc_list.currency","apc_list.value_usd","apc_paid.value","apc_paid.currency","apc_paid.value_usd",
    # citation percentiles
    "citation_normalized_percentile.value","citation_normalized_percentile.is_in_top_1_percent",
    "citation_normalized_percentile.is_in_top_10_percent","cited_by_percentile_year.min","cited_by_percentile_year.max",
    # biblio
    "biblio.volume","biblio.issue","biblio.first_page","biblio.last_page",
    # primary_topic.*
    "primary_topic.id","primary_topic.display_name","primary_topic.score","primary_topic.subfield.id",
    "primary_topic.subfield.display_name","primary_topic.field.id","primary_topic.field.display_name",
    "primary_topic.domain.id","primary_topic.domain.display_name",
    # best_oa_location — split only
    "best_oa_location.is_oa","best_oa_location.landing_page_url","best_oa_location.pdf_url",
    "best_oa_location.source.id","best_oa_location.source.display_name","best_oa_location.source.issn_l",
    "best_oa_location.source.issn","best_oa_location.source.is_oa","best_oa_location.source.is_in_doaj",
    "best_oa_location.source.is_indexed_in_scopus","best_oa_location.source.is_core",
    "best_oa_location.source.host_organization","best_oa_location.source.host_organization_name",
    "best_oa_location.source.host_organization_lineage","best_oa_location.source.host_organization_lineage_names",
    "best_oa_location.source.type","best_oa_location.license","best_oa_location.license_id",
    "best_oa_location.version","best_oa_location.is_accepted","best_oa_location.is_published",
    # abstract
    "abstract",
    # authorships.*
    "authorships.author_position","authorships.institutions","authorships.countries","authorships.is_corresponding",
    "authorships.raw_author_name","authorships.raw_affiliation_strings","authorships.affiliations",
    "authorships.author.id","authorships.author.display_name","authorships.author.orcid",
    # topics / keywords / concepts
    "topics.id","topics.display_name","topics.score","topics.subfield.id","topics.subfield.display_name",
    "topics.field.id","topics.field.display_name","topics.domain.id","topics.domain.display_name",
    "keywords.id","keywords.display_name","keywords.score",
    "concepts.id","concepts.wikidata","concepts.display_name","concepts.level","concepts.score",
    # MeSH placed after concepts.*
    "mesh.descriptor_ui","mesh.descriptor_name","mesh.qualifier_ui","mesh.qualifier_name","mesh.is_major_topic",
    # locations.*
    "locations.is_oa","locations.landing_page_url","locations.pdf_url","locations.license","locations.license_id",
    "locations.version","locations.is_accepted","locations.is_published","locations.source.id",
    "locations.source.display_name","locations.source.issn_l","locations.source.issn","locations.source.is_oa",
    "locations.source.is_in_doaj","locations.source.is_indexed_in_scopus","locations.source.is_core",
    "locations.source.host_organization","locations.source.host_organization_name",
    "locations.source.host_organization_lineage","locations.source.host_organization_lineage_names",
    "locations.source.type",
    # SDGs placed after locations.source.* and before grants.*
    "sustainable_development_goals.id","sustainable_development_goals.display_name","sustainable_development_goals.score",
    # grants.*
    "grants.funder","grants.funder_display_name","grants.award_id"
]

# ==============================
# Helpers
# ==============================
_WS_RE = re.compile(r"[ \t\r\n]+")

def clean_text(s: Optional[str]) -> Optional[str]:
    """FR: Nettoie retours de ligne/chariot/tabulations et compacte les espaces.
       EN: Remove newlines/carriage returns/tabs and collapse whitespace."""
    if s is None:
        return None
    if not isinstance(s, str):
        return s
    return _WS_RE.sub(" ", s).strip()

def norm_none(v: Any, cell_missing: str) -> str:
    """FR: Convertit None/NaN -> cell_missing ; EN: Normalize None/NaN -> cell_missing."""
    if v is None:
        return cell_missing
    if isinstance(v, float) and math.isnan(v):
        return cell_missing
    return v

def fmt_bool(v: Any, style: str, cell_missing: str) -> str:
    """FR: Formate un booléen selon le style demandé.
       EN: Format a boolean according to the requested style.
       DEFAULT: English 'True' / 'False' (original value)."""
    if v is None:
        return cell_missing
    if not isinstance(v, bool):
        return str(v)
    if style == "fr":
        return "Vrai" if v else "Faux"
    return "True" if v else "False"

def join_list(items: Optional[List[Any]], sep: str, cell_missing: str, token_missing: str) -> str:
    """
    FR: Joint une liste en remplaçant chaque jeton vide par token_missing pour éviter '||'.
        Si la liste entière est vide/absente → retourne cell_missing.
        Si tous les jetons normalisés valent token_missing → retourne UN SEUL token_missing.
    EN: Join a list replacing any empty token by token_missing to prevent '||'.
        If the whole list is empty/missing → return cell_missing.
        If all normalized tokens equal token_missing → return a SINGLE token_missing.
    """
    if items is None or len(items) == 0:
        return cell_missing
    tokens: List[str] = []
    for x in items:
        if x is None:
            tokens.append(token_missing); continue
        s = str(x).strip()
        tokens.append(s if s != "" else token_missing)
    if all(t == token_missing for t in tokens):
        return token_missing
    return sep.join(tokens)

def repr_or_empty(obj: Any, cell_missing: str) -> str:
    """FR: repr(obj) ou cell_missing si None ; EN: repr(obj) or cell_missing if None."""
    return cell_missing if obj is None else repr(obj)

def get(d: Dict[str, Any], path: List[str]) -> Any:
    """FR: Accès sûr aux sous-clés 'a.b.c'.
       EN: Safe access to nested keys 'a.b.c'."""
    cur: Any = d
    for p in path:
        if cur is None or not isinstance(cur, (dict, list)):
            return None
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur

def rebuild_abstract(abstract_inv_idx: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """FR: Reconstruit l'abstract depuis abstract_inverted_index.
       EN: Rebuild abstract from abstract_inverted_index."""
    if not abstract_inv_idx:
        return None
    max_pos = -1
    for positions in abstract_inv_idx.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    if max_pos < 0:
        return None
    words = [""] * (max_pos + 1)
    for term, positions in abstract_inv_idx.items():
        for pos in positions:
            words[pos] = term
    return " ".join(w for w in words if w)

def fmt_institution_entry(inst: Dict[str, Any]) -> str:
    """
    FR: Formate une institution: id, "display_name", ror, country_code, type, ['lin1','lin2']
    EN: Format one institution: id, "display_name", ror, country_code, type, ['lin1','lin2']
    """
    iid = inst.get("id") or ""
    name = clean_text(inst.get("display_name") or "")
    ror = inst.get("ror") or ""
    cc = inst.get("country_code") or ""
    itype = inst.get("type") or ""
    lineage = inst.get("lineage") or []
    return f"{iid}, \"{name}\", {ror}, {cc}, {itype}, {repr(lineage)}"

def fmt_affiliation_entry(aff: Dict[str, Any]) -> str:
    """
    FR: Formate une affiliation: "raw_affiliation_string", ['inst_id1','inst_id2']
    EN: Format one affiliation: "raw_affiliation_string", ['inst_id1','inst_id2']
    """
    raw = clean_text(aff.get("raw_affiliation_string") or "")
    inst_ids = aff.get("institution_ids") or []
    return f"\"{raw}\", {repr(inst_ids)}"

# ==============================
# Flatteners / Aplatisseurs
# ==============================
def flatten_ids(work: Dict[str, Any], key: str, cell_missing: str) -> str:
    """FR/EN: ids.* helper."""
    ids = work.get("ids") or {}
    return norm_none(ids.get(key), cell_missing)

def flatten_indexed_in(work: Dict[str, Any], sep: str, cell_missing: str, token_missing: str) -> str:
    """FR/EN: indexed_in as '|'-joined list."""
    return join_list(work.get("indexed_in") or [], sep, cell_missing, token_missing)

def flatten_lists_of_urls(work: Dict[str, Any], key: str, sep: str, cell_missing: str, token_missing: str) -> str:
    """FR/EN: Generic list-of-URLs flattener."""
    return join_list(work.get(key) or [], sep, cell_missing, token_missing)

def flatten_authorships(work: Dict[str, Any], list_sep: str, inner_sep: str,
                        bool_style: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """
    FR: Aplati les auteurs avec formats compacts et alignement par auteur:
        - institutions: TOUTES les institutions d'un auteur, séparées par ';'
          chaque institution: id, "display_name", ror, country_code, type, ['...']
          si aucune institution -> token_missing
        - affiliations: TOUTES les affiliations d'un auteur, séparées par ';'
          chaque affiliation: "raw_affiliation_string", ['inst_id1', ...]
          si aucune affiliation -> token_missing
        - ORCID manquant -> token_missing
        - champs 'raw*' nettoyés
    EN: Flatten authors with compact formatting and per-author alignment:
        - institutions: ALL institutions per author, separated by ';'
          each as: id, "display_name", ror, country_code, type, ['...']
          if none -> token_missing
        - affiliations: ALL affiliations per author, separated by ';'
          each as: "raw_affiliation_string", ['inst_id1', ...]
          if none -> token_missing
        - missing ORCID -> token_missing
        - 'raw*' fields cleaned
    """
    auths = work.get("authorships") or []
    positions: List[Any] = []
    insts_fmt: List[str] = []
    countries: List[str] = []
    is_corr: List[str] = []
    raw_names: List[str] = []
    raw_affils_strings: List[str] = []
    affils_fmt: List[str] = []
    a_ids: List[Any] = []
    a_names: List[Any] = []
    a_orcids: List[str] = []

    for a in auths:
        positions.append(a.get("author_position"))
        countries.append(join_list(a.get("countries") or [], list_sep, cell_missing, token_missing))
        is_corr.append(fmt_bool(a.get("is_corresponding"), bool_style, cell_missing))

        raw_names.append(clean_text(a.get("raw_author_name")) or cell_missing)
        raw_affils_list = a.get("raw_affiliation_strings") or []
        raw_affils_strings.append(join_list([clean_text(x) for x in raw_affils_list], list_sep, cell_missing, token_missing))

        inst_list = a.get("institutions") or []
        if inst_list:
            inst_tokens = [fmt_institution_entry(it) for it in inst_list]
            insts_fmt.append(inner_sep.join(inst_tokens))
        else:
            insts_fmt.append(token_missing)

        aff_list = a.get("affiliations") or []
        if aff_list:
            aff_tokens = [fmt_affiliation_entry(it) for it in aff_list]
            affils_fmt.append(inner_sep.join(aff_tokens))
        else:
            affils_fmt.append(token_missing)

        author = a.get("author") or {}
        a_ids.append(author.get("id"))
        a_names.append(author.get("display_name"))
        a_orcids.append(author.get("orcid") or token_missing)

    return {
        "authorships.author_position": join_list(positions, list_sep, cell_missing, token_missing),
        "authorships.institutions": join_list(insts_fmt, list_sep, cell_missing, token_missing),
        "authorships.countries": join_list(countries, list_sep, cell_missing, token_missing),
        "authorships.is_corresponding": join_list(is_corr, list_sep, cell_missing, token_missing),
        "authorships.raw_author_name": join_list(raw_names, list_sep, cell_missing, token_missing),
        "authorships.raw_affiliation_strings": join_list(raw_affils_strings, list_sep, cell_missing, token_missing),
        "authorships.affiliations": join_list(affils_fmt, list_sep, cell_missing, token_missing),
        "authorships.author.id": join_list(a_ids, list_sep, cell_missing, token_missing),
        "authorships.author.display_name": join_list(a_names, list_sep, cell_missing, token_missing),
        "authorships.author.orcid": join_list(a_orcids, list_sep, cell_missing, token_missing),
    }

def flatten_topics(work: Dict[str, Any], list_sep: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Flatten topics block."""
    topics = work.get("topics") or []
    ids = []; names = []; scores = []; sf_ids = []; sf_names = []; f_ids = []; f_names = []; d_ids = []; d_names = []
    for t in topics:
        ids.append(t.get("id")); names.append(t.get("display_name")); scores.append(t.get("score"))
        sub = (t.get("subfield") or {}); field = (t.get("field") or {}); dom = (t.get("domain") or {})
        sf_ids.append(sub.get("id")); sf_names.append(sub.get("display_name"))
        f_ids.append(field.get("id")); f_names.append(field.get("display_name"))
        d_ids.append(dom.get("id")); d_names.append(dom.get("display_name"))
    return {
        "topics.id": join_list(ids, list_sep, cell_missing, token_missing),
        "topics.display_name": join_list(names, list_sep, cell_missing, token_missing),
        "topics.score": join_list(scores, list_sep, cell_missing, token_missing),
        "topics.subfield.id": join_list(sf_ids, list_sep, cell_missing, token_missing),
        "topics.subfield.display_name": join_list(sf_names, list_sep, cell_missing, token_missing),
        "topics.field.id": join_list(f_ids, list_sep, cell_missing, token_missing),
        "topics.field.display_name": join_list(f_names, list_sep, cell_missing, token_missing),
        "topics.domain.id": join_list(d_ids, list_sep, cell_missing, token_missing),
        "topics.domain.display_name": join_list(d_names, list_sep, cell_missing, token_missing),
    }

def flatten_keywords(work: Dict[str, Any], list_sep: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Flatten keywords block."""
    kws = work.get("keywords") or []
    ids = []; names = []; scores = []
    for k in kws:
        ids.append(k.get("id")); names.append(k.get("display_name")); scores.append(k.get("score"))
    return {
        "keywords.id": join_list(ids, list_sep, cell_missing, token_missing),
        "keywords.display_name": join_list(names, list_sep, cell_missing, token_missing),
        "keywords.score": join_list(scores, list_sep, cell_missing, token_missing),
    }

def flatten_concepts(work: Dict[str, Any], list_sep: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Flatten concepts block."""
    cs = work.get("concepts") or []
    ids = []; wikidata = []; names = []; levels = []; scores = []
    for c in cs:
        ids.append(c.get("id")); wikidata.append(c.get("wikidata")); names.append(c.get("display_name"))
        levels.append(c.get("level")); scores.append(c.get("score"))
    return {
        "concepts.id": join_list(ids, list_sep, cell_missing, token_missing),
        "concepts.wikidata": join_list(wikidata, list_sep, cell_missing, token_missing),
        "concepts.display_name": join_list(names, list_sep, cell_missing, token_missing),
        "concepts.level": join_list(levels, list_sep, cell_missing, token_missing),
        "concepts.score": join_list(scores, list_sep, cell_missing, token_missing),
    }

def flatten_mesh_split(work: Dict[str, Any], list_sep: str, bool_style: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Flatten MeSH arrays into parallel pipe-joined lists."""
    ms = work.get("mesh") or []
    d_ui = []; d_name = []; q_ui = []; q_name = []; major = []
    for m in ms:
        d_ui.append(m.get("descriptor_ui"))
        d_name.append(m.get("descriptor_name"))
        q_ui.append(m.get("qualifier_ui"))
        q_name.append(m.get("qualifier_name"))
        major.append(fmt_bool(m.get("is_major_topic"), bool_style, cell_missing))
    return {
        "mesh.descriptor_ui": join_list(d_ui, list_sep, cell_missing, token_missing),
        "mesh.descriptor_name": join_list(d_name, list_sep, cell_missing, token_missing),
        "mesh.qualifier_ui": join_list(q_ui, list_sep, cell_missing, token_missing),
        "mesh.qualifier_name": join_list(q_name, list_sep, cell_missing, token_missing),
        "mesh.is_major_topic": join_list(major, list_sep, cell_missing, token_missing),
    }

def flatten_locations(work: Dict[str, Any], list_sep: str, bool_style: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Flatten locations into parallel pipe-joined lists with inner missing tokens."""
    locs = work.get("locations") or []
    is_oa = []; landing = []; pdf = []
    lic = []; lic_id = []; ver = []
    is_acc = []; is_pub = []
    s_id = []; s_name = []
    s_issn_l = []; s_issn = []
    s_is_oa = []; s_in_doaj = []; s_in_scopus = []; s_is_core = []
    s_host = []; s_host_name = []
    s_host_lin = []; s_host_lin_names = []; s_type = []

    for L in locs:
        is_oa.append(fmt_bool(L.get("is_oa"), bool_style, cell_missing))
        landing.append(L.get("landing_page_url"))
        pdf.append(L.get("pdf_url"))

        lic.append(L.get("license") if L.get("license") not in (None, "") else token_missing)
        lic_id.append(L.get("license_id") if L.get("license_id") not in (None, "") else token_missing)
        ver.append(L.get("version") if L.get("version") not in (None, "") else token_missing)

        is_acc.append(fmt_bool(L.get("is_accepted"), bool_style, cell_missing))
        is_pub.append(fmt_bool(L.get("is_published"), bool_style, cell_missing))

        src = L.get("source") or {}
        s_id.append(src.get("id"))
        s_name.append(src.get("display_name"))

        s_issn_l.append(src.get("issn_l") if src.get("issn_l") not in (None, "") else token_missing)
        s_issn.append(join_list(src.get("issn") or [], list_sep, cell_missing, token_missing))
        s_is_oa.append(fmt_bool(src.get("is_oa"), bool_style, cell_missing))
        s_in_doaj.append(fmt_bool(src.get("is_in_doaj"), bool_style, cell_missing))
        s_in_scopus.append(fmt_bool(src.get("is_indexed_in_scopus"), bool_style, cell_missing))
        s_is_core.append(fmt_bool(src.get("is_core"), bool_style, cell_missing))

        s_host.append(src.get("host_organization") if src.get("host_organization") not in (None, "") else token_missing)
        s_host_name.append(src.get("host_organization_name") if src.get("host_organization_name") not in (None, "") else token_missing)
        s_host_lin.append(join_list(src.get("host_organization_lineage") or [], list_sep, cell_missing, token_missing))
        s_host_lin_names.append(join_list(src.get("host_organization_lineage_names") or [], list_sep, cell_missing, token_missing))
        s_type.append(src.get("type"))

    return {
        "locations.is_oa": join_list(is_oa, list_sep, cell_missing, token_missing),
        "locations.landing_page_url": join_list(landing, list_sep, cell_missing, token_missing),
        "locations.pdf_url": join_list(pdf, list_sep, cell_missing, token_missing),
        "locations.license": join_list(lic, list_sep, cell_missing, token_missing),
        "locations.license_id": join_list(lic_id, list_sep, cell_missing, token_missing),
        "locations.version": join_list(ver, list_sep, cell_missing, token_missing),
        "locations.is_accepted": join_list(is_acc, list_sep, cell_missing, token_missing),
        "locations.is_published": join_list(is_pub, list_sep, cell_missing, token_missing),
        "locations.source.id": join_list(s_id, list_sep, cell_missing, token_missing),
        "locations.source.display_name": join_list(s_name, list_sep, cell_missing, token_missing),
        "locations.source.issn_l": join_list(s_issn_l, list_sep, cell_missing, token_missing),
        "locations.source.issn": join_list(s_issn, list_sep, cell_missing, token_missing),
        "locations.source.is_oa": join_list(s_is_oa, list_sep, cell_missing, token_missing),
        "locations.source.is_in_doaj": join_list(s_in_doaj, list_sep, cell_missing, token_missing),
        "locations.source.is_indexed_in_scopus": join_list(s_in_scopus, list_sep, cell_missing, token_missing),
        "locations.source.is_core": join_list(s_is_core, list_sep, cell_missing, token_missing),
        "locations.source.host_organization": join_list(s_host, list_sep, cell_missing, token_missing),
        "locations.source.host_organization_name": join_list(s_host_name, list_sep, cell_missing, token_missing),
        "locations.source.host_organization_lineage": join_list(s_host_lin, list_sep, cell_missing, token_missing),
        "locations.source.host_organization_lineage_names": join_list(s_host_lin_names, list_sep, cell_missing, token_missing),
        "locations.source.type": join_list(s_type, list_sep, cell_missing, token_missing),
    }

def flatten_best_oa_location(work: Dict[str, Any], bool_style: str, cell_missing: str, list_sep: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Split best_oa_location into explicit scalar columns."""
    b = work.get("best_oa_location") or None
    out: Dict[str, str] = {}
    keys = {
        "best_oa_location.is_oa": lambda x: fmt_bool(x.get("is_oa"), bool_style, cell_missing),
        "best_oa_location.landing_page_url": lambda x: x.get("landing_page_url") or cell_missing,
        "best_oa_location.pdf_url": lambda x: x.get("pdf_url") or cell_missing,
        "best_oa_location.license": lambda x: x.get("license") or cell_missing,
        "best_oa_location.license_id": lambda x: x.get("license_id") or cell_missing,
        "best_oa_location.version": lambda x: x.get("version") or cell_missing,
        "best_oa_location.is_accepted": lambda x: fmt_bool(x.get("is_accepted"), bool_style, cell_missing),
        "best_oa_location.is_published": lambda x: fmt_bool(x.get("is_published"), bool_style, cell_missing),
    }
    if not b:
        for k in keys:
            out[k] = cell_missing
        for k in [
            "best_oa_location.source.id","best_oa_location.source.display_name","best_oa_location.source.issn_l",
            "best_oa_location.source.issn","best_oa_location.source.is_oa","best_oa_location.source.is_in_doaj",
            "best_oa_location.source.is_indexed_in_scopus","best_oa_location.source.is_core",
            "best_oa_location.source.host_organization","best_oa_location.source.host_organization_name",
            "best_oa_location.source.host_organization_lineage","best_oa_location.source.host_organization_lineage_names",
            "best_oa_location.source.type"
        ]:
            out[k] = cell_missing
        return out

    for k, fn in keys.items():
        out[k] = fn(b)

    src = b.get("source") or {}
    out["best_oa_location.source.id"] = src.get("id") or cell_missing
    out["best_oa_location.source.display_name"] = src.get("display_name") or cell_missing
    out["best_oa_location.source.issn_l"] = src.get("issn_l") or cell_missing
    out["best_oa_location.source.issn"] = join_list(src.get("issn") or [], list_sep, cell_missing, token_missing)
    out["best_oa_location.source.is_oa"] = fmt_bool(src.get("is_oa"), bool_style, cell_missing)
    out["best_oa_location.source.is_in_doaj"] = fmt_bool(src.get("is_in_doaj"), bool_style, cell_missing)
    out["best_oa_location.source.is_indexed_in_scopus"] = fmt_bool(src.get("is_indexed_in_scopus"), bool_style, cell_missing)
    out["best_oa_location.source.is_core"] = fmt_bool(src.get("is_core"), bool_style, cell_missing)
    out["best_oa_location.source.host_organization"] = src.get("host_organization") or cell_missing
    out["best_oa_location.source.host_organization_name"] = src.get("host_organization_name") or cell_missing
    out["best_oa_location.source.host_organization_lineage"] = join_list(src.get("host_organization_lineage") or [], list_sep, cell_missing, token_missing)
    out["best_oa_location.source.host_organization_lineage_names"] = join_list(src.get("host_organization_lineage_names") or [], list_sep, cell_missing, token_missing)
    out["best_oa_location.source.type"] = src.get("type") or cell_missing
    return out

def flatten_counts_by_year(work: Dict[str, Any], list_sep: str, cell_missing: str, token_missing: str) -> Dict[str, str]:
    """FR/EN: Split counts_by_year into parallel year and cited_by_count lists."""
    cby = work.get("counts_by_year") or []
    years = []; counts = []
    for it in cby:
        if isinstance(it, dict):
            years.append(it.get("year"))
            counts.append(it.get("cited_by_count"))
    return {
        "counts_by_year.year": join_list(years, list_sep, cell_missing, token_missing),
        "counts_by_year.cited_by_count": join_list(counts, list_sep, cell_missing, token_missing),
    }

# ==============================
# Mapping principal / Main row mapping
# ==============================
def to_row(work: Dict[str, Any], list_sep: str, inner_sep: str, bool_style: str, cell_missing: str, token_missing: str) -> Dict[str, Any]:
    """FR: Produit un dict colonne→valeur pour une notice.
       EN: Produce a column→value dict for one work record."""
    row: Dict[str, Any] = {}

    direct_map = {
        "id":"id","doi":"doi","title":"title","display_name":"display_name",
        "publication_year":"publication_year","publication_date":"publication_date",
        "language":"language","type":"type","type_crossref":"type_crossref",
        "countries_distinct_count":"countries_distinct_count","institutions_distinct_count":"institutions_distinct_count",
        "fwci":"fwci","has_fulltext":"has_fulltext","fulltext_origin":"fulltext_origin",
        "cited_by_count":"cited_by_count","is_retracted":"is_retracted","is_paratext":"is_paratext",
        "locations_count":"locations_count","cited_by_api_url":"cited_by_api_url",
        "updated_date":"updated_date","created_date":"created_date",
        "biblio.volume":"biblio.volume","biblio.issue":"biblio.issue",
        "biblio.first_page":"biblio.first_page","biblio.last_page":"biblio.last_page",
        "primary_topic.id":"primary_topic.id","primary_topic.display_name":"primary_topic.display_name",
        "primary_topic.score":"primary_topic.score","primary_topic.subfield.id":"primary_topic.subfield.id",
        "primary_topic.subfield.display_name":"primary_topic.subfield.display_name",
        "primary_topic.field.id":"primary_topic.field.id","primary_topic.field.display_name":"primary_topic.field.display_name",
        "primary_topic.domain.id":"primary_topic.domain.id","primary_topic.domain.display_name":"primary_topic.domain.display_name",
    }
    for out_col, path_str in direct_map.items():
        val = get(work, path_str.split(".")) if "." in path_str else work.get(path_str)

        # Nettoyage pour titres / Title cleanup
        if out_col in ("title", "display_name") and isinstance(val, str):
            val = clean_text(val)

        # Nettoyage générique pour raw* / Generic cleanup for raw*
        if out_col.startswith("raw"):
            if isinstance(val, list):
                val = [clean_text(x) if isinstance(x, str) else x for x in val]
            elif isinstance(val, str):
                val = clean_text(val)

        if isinstance(val, bool):
            row[out_col] = fmt_bool(val, bool_style, cell_missing)
        elif isinstance(val, list):
            row[out_col] = join_list(val, list_sep, cell_missing, token_missing)
        elif isinstance(val, dict):
            row[out_col] = repr_or_empty(val, cell_missing)
        else:
            row[out_col] = norm_none(val, cell_missing)

    # counts_by_year
    row.update(flatten_counts_by_year(work, list_sep, cell_missing, token_missing))

    # datasets/versions/reference links
    row["datasets"] = repr_or_empty(work.get("datasets"), cell_missing)
    row["versions"] = repr_or_empty(work.get("versions"), cell_missing)
    row["referenced_works_count"] = norm_none(work.get("referenced_works_count"), cell_missing)
    row["referenced_works"] = flatten_lists_of_urls(work, "referenced_works", list_sep, cell_missing, token_missing)
    row["related_works"] = flatten_lists_of_urls(work, "related_works", list_sep, cell_missing, token_missing)

    # ids.*
    row["ids.openalex"] = flatten_ids(work, "openalex", cell_missing)
    row["ids.doi"] = flatten_ids(work, "doi", cell_missing)
    row["ids.mag"] = flatten_ids(work, "mag", cell_missing)
    row["ids.pmid"] = flatten_ids(work, "pmid", cell_missing)
    row["ids.pmcid"] = flatten_ids(work, "pmcid", cell_missing)

    # indexed_in / assertions / corresponding groups
    row["indexed_in"] = flatten_indexed_in(work, list_sep, cell_missing, token_missing)
    row["institution_assertions"] = cell_missing
    row["corresponding_author_ids"] = join_list(work.get("corresponding_author_ids") or [], list_sep, cell_missing, token_missing)
    row["corresponding_institution_ids"] = join_list(work.get("corresponding_institution_ids") or [], list_sep, cell_missing, token_missing)

    # primary_location.*
    pl = work.get("primary_location") or {}
    pls = pl.get("source") or {}
    row["primary_location.is_oa"] = fmt_bool(pl.get("is_oa"), bool_style, cell_missing)
    row["primary_location.landing_page_url"] = pl.get("landing_page_url") or cell_missing
    row["primary_location.pdf_url"] = pl.get("pdf_url") or cell_missing
    row["primary_location.source.id"] = pls.get("id") or cell_missing
    row["primary_location.source.display_name"] = pls.get("display_name") or cell_missing
    row["primary_location.source.issn_l"] = pls.get("issn_l") or cell_missing
    row["primary_location.source.issn"] = join_list(pls.get("issn") or [], list_sep, cell_missing, token_missing)
    row["primary_location.source.is_oa"] = fmt_bool(pls.get("is_oa"), bool_style, cell_missing)
    row["primary_location.source.is_in_doaj"] = fmt_bool(pls.get("is_in_doaj"), bool_style, cell_missing)
    row["primary_location.source.is_indexed_in_scopus"] = fmt_bool(pls.get("is_indexed_in_scopus"), bool_style, cell_missing)
    row["primary_location.source.is_core"] = fmt_bool(pls.get("is_core"), bool_style, cell_missing)
    row["primary_location.source.host_organization"] = pls.get("host_organization") or cell_missing
    row["primary_location.source.host_organization_name"] = pls.get("host_organization_name") or cell_missing
    row["primary_location.source.host_organization_lineage"] = join_list(pls.get("host_organization_lineage") or [], list_sep, cell_missing, token_missing)
    row["primary_location.source.host_organization_lineage_names"] = join_list(pls.get("host_organization_lineage_names") or [], list_sep, cell_missing, token_missing)
    row["primary_location.source.type"] = pls.get("type") or cell_missing
    row["primary_location.license"] = pl.get("license") or cell_missing
    row["primary_location.license_id"] = pl.get("license_id") or cell_missing
    row["primary_location.version"] = pl.get("version") or cell_missing
    row["primary_location.is_accepted"] = fmt_bool(pl.get("is_accepted"), bool_style, cell_missing)
    row["primary_location.is_published"] = fmt_bool(pl.get("is_published"), bool_style, cell_missing)

    # open_access.*
    oa = work.get("open_access") or {}
    row["open_access.is_oa"] = fmt_bool(oa.get("is_oa"), bool_style, cell_missing)
    row["open_access.oa_status"] = oa.get("oa_status") or cell_missing
    row["open_access.oa_url"] = oa.get("oa_url") or cell_missing
    row["open_access.any_repository_has_fulltext"] = fmt_bool(oa.get("any_repository_has_fulltext"), bool_style, cell_missing)

    # APCs
    apcl = work.get("apc_list") or {}
    row["apc_list.value"] = apcl.get("value") if apcl.get("value") is not None else cell_missing
    row["apc_list.currency"] = apcl.get("currency") or cell_missing
    row["apc_list.value_usd"] = apcl.get("value_usd") if apcl.get("value_usd") is not None else cell_missing

    apcp = work.get("apc_paid") or {}
    row["apc_paid.value"] = apcp.get("value") if apcp.get("value") is not None else cell_missing
    row["apc_paid.currency"] = apcp.get("currency") or cell_missing
    row["apc_paid.value_usd"] = apcp.get("value_usd") if apcp.get("value_usd") is not None else cell_missing

    # Citation percentiles
    cnp = work.get("citation_normalized_percentile") or {}
    row["citation_normalized_percentile.value"] = cnp.get("value") if cnp.get("value") is not None else cell_missing
    row["citation_normalized_percentile.is_in_top_1_percent"] = fmt_bool(cnp.get("is_in_top_1_percent"), bool_style, cell_missing)
    row["citation_normalized_percentile.is_in_top_10_percent"] = fmt_bool(cnp.get("is_in_top_10_percent"), bool_style, cell_missing)

    cpy = work.get("cited_by_percentile_year") or {}
    row["cited_by_percentile_year.min"] = cpy.get("min") if cpy.get("min") is not None else cell_missing
    row["cited_by_percentile_year.max"] = cpy.get("max") if cpy.get("max") is not None else cell_missing

    # best_oa_location
    row.update(flatten_best_oa_location(work, bool_style, cell_missing, list_sep, token_missing))

    # Abstract
    abstract_txt = rebuild_abstract(work.get("abstract_inverted_index")) or work.get("abstract")
    row["abstract"] = clean_text(abstract_txt) if isinstance(abstract_txt, str) else norm_none(abstract_txt, cell_missing)

    # Blocs multiples
    row.update(flatten_authorships(work, list_sep, "; ", bool_style, cell_missing, token_missing))
    row.update(flatten_topics(work, list_sep, cell_missing, token_missing))
    row.update(flatten_keywords(work, list_sep, cell_missing, token_missing))
    row.update(flatten_concepts(work, list_sep, cell_missing, token_missing))
    row.update(flatten_mesh_split(work, list_sep, bool_style, cell_missing, token_missing))
    row.update(flatten_locations(work, list_sep, bool_style, cell_missing, token_missing))

    # SDGs
    sdgs = work.get("sustainable_development_goals") or []
    row["sustainable_development_goals.id"] = join_list([s.get("id") for s in sdgs], list_sep, cell_missing, token_missing)
    row["sustainable_development_goals.display_name"] = join_list([s.get("display_name") for s in sdgs], list_sep, cell_missing, token_missing)
    row["sustainable_development_goals.score"] = join_list([s.get("score") for s in sdgs], list_sep, cell_missing, token_missing)

    # Grants
    grants = work.get("grants") or []
    row["grants.funder"] = join_list([g.get("funder") for g in grants], list_sep, cell_missing, token_missing)
    row["grants.funder_display_name"] = join_list([g.get("funder_display_name") for g in grants], list_sep, cell_missing, token_missing)
    row["grants.award_id"] = join_list(
        [g.get("award_id") if g.get("award_id") not in (None, "") else None for g in grants],
        list_sep, cell_missing, token_missing
    )

    return row

# ==============================
# Lecture multi-formats / Multi-shape input
# ==============================
def iter_works(payload: Any) -> Iterable[Dict[str, Any]]:
    """FR: Itère sur les works selon la forme d'entrée.
       EN: Iterate over works depending on input shape."""
    if isinstance(payload, dict):
        if "results" in payload and isinstance(payload["results"], list):
            for w in payload["results"]:
                if isinstance(w, dict):
                    yield w
        else:
            yield payload
    elif isinstance(payload, list):
        for w in payload:
            if isinstance(w, dict):
                yield w

def main():
    ap = argparse.ArgumentParser(description="OpenAlex Works JSON -> CSV/TSV (custom header, multi-row)")
    ap.add_argument("--json-in", required=True, help="FR: Fichier JSON: 1 work, liste de works, ou objet API avec 'results' / EN: JSON file: one work, list of works, or API-shaped object with 'results'")
    ap.add_argument("-o", "--output", required=True, help="FR: Chemin du fichier de sortie / EN: Output file path")
    ap.add_argument("--format", choices=["csv","tsv"], default="tsv", help="FR: Format de sortie (csv|tsv, défaut: tsv) / EN: Output format (csv|tsv, default: tsv)")
    ap.add_argument("--list-sep", default="|", help="FR: Séparateur pour aplatir les listes (défaut: '|') / EN: List separator (default: '|')")
    ap.add_argument("--bool-style", choices=["en","fr"], default="en",
                    help="FR: Style booléen: en='True/False' (défaut), fr='Vrai/Faux' / EN: Boolean style")
    ap.add_argument("--cell-missing", default="", help="FR: Chaîne pour cellule totalement absente (défaut: vide) / EN: String for wholly-missing cell (default: empty)")
    ap.add_argument("--list-missing-token", default="None",
                    help="FR: Jeton de remplacement à l'intérieur des listes (défaut: 'None') / EN: Replacement token inside lists (default: 'None')")
    ap.add_argument("--log-out", default=None, help="FR: Fichier log listant les colonnes et le nombre de lignes / EN: Log file listing columns and row count")
    args = ap.parse_args()

    # Resolve missing-cell string
    cell_missing = args.cell_missing
    token_missing = args.list_missing_token

    # Choose delimiter and display name
    if args.format == "csv":
        delimiter = ","
        delim_name = "VIRGULE/COMMA"
    else:
        delimiter = "\t"
        delim_name = "TAB"

    print(f"Format: {args.format} — Delimiteur: {delim_name}")

    # Load input JSON
    with open(args.json_in, "r", encoding="utf-8") as f:
        payload = json.load(f)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write table
    with open(out_path, "w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout, delimiter=delimiter)
        writer.writerow(HEADER_COLS)
        count = 0
        for work in iter_works(payload):
            row = to_row(
                work=work,
                list_sep=args.list_sep,
                inner_sep="; ",
                bool_style=args.bool_style,
                cell_missing=cell_missing,
                token_missing=token_missing,
            )
            writer.writerow([row.get(col, cell_missing) for col in HEADER_COLS])
            count += 1

    # Log file
    log_path = Path(args.log_out) if args.log_out else out_path.with_suffix(out_path.suffix + ".log")
    with open(log_path, "w", encoding="utf-8") as flog:
        flog.write("# Columns / Colonnes\n")
        for col in HEADER_COLS:
            flog.write(f"{col}\n")
        flog.write(f"\n# Rows written / Lignes écrites: {count}\n")

    print(f"OK - écrit {count} ligne(s) dans: {out_path}")
    print(f"Log écrit dans: {log_path}")

if __name__ == "__main__":
    main()
