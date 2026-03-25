# Älykäs Opintosuunnittelija

## Summary
Tässä projektissa rakennetaan Älykäs Opintosuunnittelija, joka auttaa opiskelijaa suunnittelemaan tehokkaan aikataulun AI-avusteisesti. Building AI course project.

## Tausta
Opiskelijoilla on usein vaikeuksia suunnitella opiskeluajan käyttöä tehokkaasti, erityisesti kun hallitaan useita aineita tai määräaikoja. Huono suunnittelu voi johtaa stressiin, määräaikojen myöhästymiseen ja heikompaan oppimistulokseen.

* Ongelma 1: Tehtävien priorisointi omien suoritusten ja määräaikojen mukaan on haastavaa.  
* Ongelma 2: Tehoton opiskelu johtaa ajankäytön tuhlaukseen.  
* Ongelma 3: Puute palautteesta opiskelun tehokkuudesta.  

## Käyttötapa
Opiskelija syöttää aineet, tulevat määräajat ja arvioidun opiskeluaikatarpeen. Tekoäly analysoi aiempia opintotietoja ja ehdottaa aikataulua suositelluilla opiskelujaksoilla.  
Aikataulu sisältää:  

* Päiväkohtaiset opiskelublokit
* * Jaksojen keston ja tauot  
* Prioriteetit tärkeimmille tehtäville  
* Suositeltu aikaväli: viikko / kuukausi  

## Datalähteet ja AI-menetelmät
- **Data:** opiskelijan aiemmat opintopäiväkirjat (päivämäärä, aine, kesto, koettu tehokkuus, tulos)  
- **AI-menetelmät:** valvottu regressio ennustamaan tehokkaimmat opiskelutunnit + heuristiikka aikataulun optimointiin

```python
def ehdota_opiskeluaikataulu(opiskelijadata):
    malli = lataa_valmis_malli(opiskelijadata)
    suositellut_jaksot = optimoi_aikataulu(malli)
    return suositellut_jaksot
Add Summary
