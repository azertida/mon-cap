# Mon cap

Un compagnon de poche pour **garder le cap quand les transports déraillent** —
pensé pour les personnes âgées, en particulier les apprenant·es de l'EPN Wolu Cyber.

Tram supprimé, escalator en panne, canicule, grève : *Mon cap* n'essaie pas de
réparer le réseau. Il aide à prendre **une décision à la fois**, calmement, et
fonctionne **même sans réseau**.

> Statut : prototype / maquette. Données et contacts d'exemple encore fictifs.

---

## L'idée en bref

La personne ne diagnostique jamais sa situation : elle **se reconnaît** dans un
état formulé à la première personne (« je ne me sens pas bien », « je ne peux
plus avancer », « je ne comprends pas ce qui se passe »…). Derrière chaque état,
*Mon cap* propose un petit bouquet d'actions, déjà adapté au contexte du jour, et
toujours doublé d'un **repli humain** (« montrez ceci à quelqu'un », « appeler un
proche ») quand la technique fait défaut.

Quatre niveaux structurent tout :

- **Causes** (canicule, grève, travaux…) — infinies, jamais demandées à la personne ;
  elles ne font que *colorer* les solutions.
- **États** — finis, à la première personne : la seule porte d'entrée.
- **Besoins** — déduits par le système, jamais par la personne.
- **Solutions** — concrètes : un abri, un proche, une autre route.

## Comment ça marche

```
OpenStreetMap ──(Overpass)──> build_abris.py ──> abris.json ──> PWA (hors-ligne)
                                   ▲                                   │
                            GitHub Action                       géoloc + horloge
                            (cron décalé)                       sur l'appareil :
                                                                « le plus proche
                                                                  + ouvert ? »
```

- Les données **stables** (abris, arrêts) sont fabriquées périodiquement par une
  GitHub Action et mises en cache par la PWA → **tout le cœur marche hors-ligne**.
- Les données **volatiles** (perturbations, météo) seront ajoutées en direct quand
  il y a du réseau, avec repli sur le dernier état connu (horodaté).
- Aucune clé d'API côté client, aucune dépendance à un grand acteur.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `index.html` | La PWA (interface). |
| `manifest.json`, `service-worker.js`, `icons/` | Configuration PWA + cache hors-ligne. |
| `abris.overpassql` | La requête Overpass, testable sur [overpass-turbo.eu](https://overpass-turbo.eu). |
| `build_abris.py` | Récolte OSM → produit `abris.json` (bibliothèque standard seulement). |
| `abris.json` | **Généré par l'Action — ne pas éditer à la main.** |
| `.github/workflows/abris.yml` | Reconstruit et committe `abris.json` (cron + déclenchement manuel). |

## Régénérer les données

- **Automatique** : l'Action tourne deux fois par jour (heures volontairement
  décalées, le cron GitHub étant « best effort »).
- **Manuel** : onglet *Actions → Construire abris.json → Run workflow*.
- **En local** : `python build_abris.py --pretty`

## Données & licence

Les données d'abris proviennent d'**OpenStreetMap**, © les contributeurs
d'OpenStreetMap, sous licence **ODbL**. Toute réutilisation (y compris une fiche
imprimée) doit conserver cette attribution.

Le parsing des horaires (`opening_hours`) se fait côté appareil avec la
bibliothèque [opening_hours.js](https://github.com/opening-hours/opening_hours.js),
qui gère les jours fériés et les saisons.

## Notes de maintenance

- **Horaires réguliers seulement.** `abris.json` ne contient que des horaires
  récurrents. Les horaires *ponctuels* ou *tournants* ne doivent pas y figurer.
- **Pharmacies de garde.** L'ouverture du dimanche/la nuit est une garde
  tournante, donc **dynamique** : ne jamais l'afficher comme un horaire fixe
  (drapeau `dynamic_offhours`). Renvoyer vers la garde officielle.
- **Horaires inconnus.** Beaucoup de lieux OSM n'ont pas d'`opening_hours` :
  les afficher sans promettre qu'ils sont ouverts.
- **Vérification terrain.** Les horaires peuvent être faux. La validation se fait
  sur le terrain (atelier Wolu Cyber) ; les corrections se contribuent à OSM via
  [Every Door](https://everydoor.app) (iOS + Android), pas depuis *Mon cap*, qui
  reste en lecture seule.
- **Cron & inactivité.** GitHub désactive les crons après 60 jours d'inactivité
  du dépôt ; les commits réguliers de l'Action l'évitent.
