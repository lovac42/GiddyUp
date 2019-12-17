# GiddyUp: Block scheduling info during apkg imports


## About:
When you import a shared deck with scheduling info, imported stats are merged with your stats. Even if you delete the card(s) later on, imported stats are not purged from your collection. It stays forever!

<img src="https://github.com/lovac42/GiddyUp/blob/master/screenshots/card_info.png?raw=true">  
<i>This info stays in your collection forever!! Even if you accidentally imported someone else's scheduling information and delete the card later.</i><br><br>

<img src="https://github.com/lovac42/GiddyUp/blob/master/screenshots/stats_info.png?raw=true">  
<i>Someone else's data in my stats due to shared decks with scheduling info.</i><br><br>

The simple solution is to check whether a shared deck contains scheduling info during import. And if any are found, ask the user how to handle them. This addon lets the user decide whether to import the shared deck as is with scheduling info or to reset them as new during import. Resetting could mess up the sorting order, and the user will need to manually re-sort them in the browser afterwards.
