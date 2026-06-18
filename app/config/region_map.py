# app/config/region_map.py

"""
Definitieve gemeentekaart voor alle Turbo Services regio’s.
Wordt gebruikt door:
 - ContentEngine (SEO en teksten)
 - HeroImageEngine (regio-prompt)
 - WebsiteGenerator
 - Marketing Agent (landingspagina's)
"""

REGION_COMMUNES = {
    "antwerpen-stad": [
        "Antwerpen",
        "Berchem",
        "Borgerhout",
        "Deurne",
        "Ekeren",
        "Hoboken",
        "Merksem",
        "Wilrijk",
        "Berendrecht-Zandvliet-Lillo"
    ],

    "antwerpen-noordrand": [
        "Brasschaat",
        "Schoten",
        "Kapellen",
        "Stabroek",
        "Wuustwezel",
        "Kalmthout",
        "Brecht"
    ],

    "antwerpen-zuidrand": [
        "Edegem",
        "Hove",
        "Kontich",
        "Lint",
        "Aartselaar",
        "Hemiksem",
        "Schelle",
        "Niel"
    ],

    "ruppelstreek": [
        "Boom",
        "Rumst",
        "Schelle",
        "Niel",
        "Hemiksem"
    ],

    "klein-brabant": [
        "Bornem",
        "Puurs-Sint-Amands",
        "Willebroek"
    ],

    "waasland": [
        "Beveren",
        "Sint-Niklaas",
        "Kruibeke",
        "Temse",
        "Zwijndrecht",
        "Lokeren",
        "Stekene",
        "Sint-Gillis-Waas"
    ],

    "mechelen-rivierenland": [
        "Mechelen",
        "Bonheiden",
        "Sint-Katelijne-Waver",
        "Duffel",
        "Willebroek",
        "Zemst",
        "Lier"
    ],

    "lier-neteland": [
        "Lier",
        "Nijlen",
        "Herentals",
        "Herenthout",
        "Grobbendonk",
        "Vorselaar",
        "Olen"
    ],

    "kempen-noord": [
        "Hoogstraten",
        "Merksplas",
        "Rijkevorsel",
        "Lille",
        "Malle",
        "Vosselaar",
        "Turnhout"
    ],

    "kempen-zuid": [
        "Geel",
        "Westerlo",
        "Herselt",
        "Laakdal",
        "Hulshout",
        "Heist-op-den-Berg",
        "Mol",
        "Balen",
        "Dessel",
        "Retie"
    ],

    "brussel-centrum": [
        "Brussel-Stad",
        "Elsene",
        "Sint-Joost-ten-Node"
    ],

    "brussel-noord": [
        "Schaarbeek",
        "Evere",
        "Sint-Lambrechts-Woluwe"
    ],

    "brussel-zuid": [
        "Ukkel",
        "Vorst",
        "Watermaal-Bosvoorde"
    ],

    "noordrand-brussel": [
        "Vilvoorde",
        "Machelen",
        "Zaventem",
        "Grimbergen",
        "Wemmel",
        "Meise",
        "Kapelle-op-den-Bos"
    ],

    "druivenstreek": [
        "Hoeilaart",
        "Overijse",
        "Tervuren"
    ],

    "pajottenland": [
        "Dilbeek",
        "Lennik",
        "Gooik",
        "Galmaarden",
        "Herne",
        "Bever",
        "Pepingen"
    ],

    "leuven-dijleland": [
        "Leuven",
        "Herent",
        "Kortenberg",
        "Bertem",
        "Oud-Heverlee",
        "Huldenberg"
    ],

    "hageland": [
        "Aarschot",
        "Diest",
        "Scherpenheuvel-Zichem",
        "Tielt-Winge",
        "Bekkevoort",
        "Geetbets",
        "Kortenaken",
        "Landen"
    ],

    "durmestreek": [
        "Hamme",
        "Waasmunster",
        "Zele",
        "Lokeren"
    ],

    "sint-niklaas-regio": [
        "Sint-Niklaas",
        "Belsele",
        "Nieuwkerken-Waas",
        "Sinaai"
    ],

    "temse-omstreken": [
        "Temse",
        "Tielrode",
        "Elversele",
        "Steendorp",
        "Kruibeke"
    ],

    "denderstreek": [
        "Aalst",
        "Denderleeuw",
        "Haaltert",
        "Lede",
        "Ninove",
        "Geraardsbergen",
        "Liedekerke",
        "Affligem",
        "Herzele",
        "Zottegem"
    ],

    "scheldeland": [
        "Dendermonde",
        "Wetteren",
        "Laarne",
        "Wichelen",
        "Berlare",
        "Lebbekke",
        "Buggenhout"
    ],

    "durmestreek-lokeren": [
        "Lokeren",
        "Waasmunster",
        "Zele",
        "Hamme"
    ],

    "temse-omgeving": [
        "Temse",
        "Sint-Niklaas",
        "Beveren-Kruibeke-Zwijndrecht",
        "Bornem"
    ]
}


def get_region_communes(region_slug: str) -> list:
    region_slug = region_slug.strip().lower()
    if region_slug not in REGION_COMMUNES:
        raise KeyError(f"Geen gemeentelijst voor regio: {region_slug}")
    return REGION_COMMUNES[region_slug]
