# -*- coding: utf-8 -*-
# Copyright 2019 Lovac42
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# Support: https://github.com/lovac42/GiddyUp


from aqt.utils import askUser
from anki.utils import intTime
from anki.hooks import wrap
from anki.lang import _



def makeNew(self, cards, largest):
    cnt = largest
    for card in cards:
        card[2] = make_did(self, card[2])

        # if not new card
        if not card[6] and card[7]==-1: #new suspend
            card[6] = 0 # type
            card[7] = 0 # queue
        elif card[6] or card[7]:
            card[6] = 0 # type
            card[7] = 0 # queue
            card[8] = cnt #due

        if card[8]<0:
            card[8] = cnt #due

        # reset all odid, odue, etc...
        for i in range(9,17): #see anki.cards.py:load
            card[i] = 0
        cnt += 1
    return cards



def make_did(self, did):
    "Given did in src col, return local id."
    # already converted?
    if did in self._decks:
        return self._decks[did]
    # get the name in src
    g = self.src.decks.get(did)
    name = g['name']
    # if there's a prefix, replace the top level deck
    if self.deckPrefix:
        tmpname = "::".join(name.split("::")[1:])
        name = self.deckPrefix
        if tmpname:
            name += "::" + tmpname
    # manually create any parents so we can pull in descriptions
    head = ""
    for parent in name.split("::")[:-1]:
        if head:
            head += "::"
        head += parent
        idInSrc = self.src.decks.id(head)
        self._did(idInSrc)
    # if target is a filtered deck, we'll need a new deck name
    deck = self.dst.decks.byName(name)
    if deck and deck['dyn']:
        name = "%s %d" % (name, intTime())
    # create in local
    newid = self.dst.decks.id(name)
    # save desc
    deck = self.dst.decks.get(newid)
    deck['desc'] = g['desc']
    self.dst.decks.save(deck)
    # add to deck map and return
    self._decks[did] = newid
    return newid


def wrap_importCards(self, _old):
    # build map of (guid, ord) -> cid and used id cache
    self._cards = {}
    existing = {}
    for guid, ord, cid in self.dst.db.execute(
        "select f.guid, c.ord, c.id from cards c, notes f "
        "where c.nid = f.id"):
        existing[cid] = True
        self._cards[(guid, ord)] = cid
    # loop through src
    revFound = False
    cards = []
    revlog = []
    largest = 0
    usn = self.dst.usn()
    aheadBy = self.src.sched.today - self.dst.sched.today
    for card in self.src.db.execute(
        "select f.guid, f.mid, c.* from cards c, notes f "
        "where c.nid = f.id"):
        guid = card[0]
        if guid in self._changedGuids:
            guid = self._changedGuids[guid]
        if guid in self._ignoredGuids:
            continue
        # does the card's note exist in dst col?
        if guid not in self._notes:
            continue
        dnid = self._notes[guid]
        # does the card already exist in the dst col?
        ord = card[5]
        if (guid, ord) in self._cards:
            # fixme: in future, could update if newer mod time
            continue
        # doesn't exist. strip off note info, and save src id for later
        card = list(card[2:])
        scid = card[0]
        # ensure the card id is unique
        while card[0] in existing:
            card[0] += 999
        existing[card[0]] = True
        # update cid, nid, etc
        card[1] = self._notes[guid][0]
        card[4] = intTime()
        card[5] = usn
        if card[6] or card[7] or card[11]:
            revFound = True
        # review cards have a due date relative to collection
        if card[7] in (2, 3) or card[6] == 2:
            card[8] -= aheadBy
        # odue needs updating too
        if card[14]:
            card[14] -= aheadBy
        # if odid true, convert card from filtered to normal
        if card[15]:
            # odid
            card[15] = 0
            # odue
            card[8] = card[14]
            card[14] = 0
            # queue
            if card[6] == 1: # type
                card[6] = 0
                card[7] = 0
            else:
                card[7] = card[6]
        cards.append(card)
        # we need to import revlog, rewriting card ids and bumping usn
        for rev in self.src.db.execute(
            "select * from revlog where cid = ?", scid):
            rev = list(rev)
            rev[1] = card[0]
            rev[2] = self.dst.usn()
            revlog.append(rev)

        if card[8] > largest:
            largest = card[8]

    if (revlog or revFound) and \
    not askUser(
            _("Import scheduling information?<br>No will rest cards as new."),
            defaultno=True,
            title="Scheduling information detected"
        ):
        cards = makeNew(self, cards, largest)
        revlog = []
    else:
        for card in cards:
            card[2] = self._did(card[2])

    # apply
    self.dst.db.executemany("""
insert or ignore into cards values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", cards)
    self.dst.db.executemany("""
insert or ignore into revlog values (?,?,?,?,?,?,?,?,?)""", revlog)





from anki.importing.apkg import AnkiPackageImporter
AnkiPackageImporter._importCards=wrap(
    AnkiPackageImporter._importCards,
    wrap_importCards,
    "around"
)

