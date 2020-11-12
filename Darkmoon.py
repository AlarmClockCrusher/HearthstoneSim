from CardTypes import *
from Triggers_Auras import *

from Basic import IllidariInitiate, Huffer, Leokk, Misha
from Classic import YourNextSpellCosts2LessThisTurn

from numpy.random import choice as npchoice
from numpy.random import randint as nprandint
from collections import Counter as cnt
import copy

"""Madness at the Darkmoon Faire"""
class Trig_Corrupt(TrigHand):
	def __init__(self, entity, corruptedType):
		self.blank_init(entity, ["ManaPaid"])
		self.corruptedType = corruptedType
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand and ID == self.entity.ID and number > self.entity.mana
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		card = self.entity
		newCard = self.corruptedType(card.Game, card.ID)
		#Buff and mana effects, etc, will be preserved
		#Buff to cards in hand will always be permanent or temporary, not from Auras
		if newCard == "Minion":
			#Temporary attack changes on minions are NOT included in attack_Enchant
			attBuff, healthBuff = card.attack_Enchant - card.attack_0, card.health_Enchant - card.health_0
			newCard.buffDebuff(attBuff, healthBuff)
			for attGain, attRevertTime in card.tempAttChanges:
				newCard.buffDebuff(attGain, 0, attRevertTime)
		elif newCard == "Weapon": #Only applicable to Felsteel Executioner
			attBuff, healthBuff = card.attack_Enchant - card.attack_0, card.health_Enchant - card.health_0
			#Assume temporary attack changes applied on a minion won't carry over to the weapon
			newCard.gainStat(attBuff, healthBuff)
		#Find keywords the new card doesn't have
		keyWords = newCard.keyWords.keys()
		for key, value in newCard.keyWords.items():
			if value < 1 and card.keyWords[key] > 0: newCard.keyWords[key] = 1
		for key, value in newCard.marks.items():
			if value < 1 and card.marks[key] > 0: newCard.marks[key] = 1
		newCard.trigsHand += [trig for trig in card.trigsHand if not isinstance(trig, Trig_Corrupt)]
		#There are no Corrupted cards with predefined Deathrattles
		newCard.deathrattles = [type(deathrattle)(newCard) for deathrattle in card.deathrattles]
		#Mana modifications
		newCard.manaMods = [manaMod.selfCopy(newCard) for manaMod in card.manaMods]
		
		card.Game.Hand_Deck.replaceCardinHand(card, newCard)
		
"""Mana 1 cards"""
class SafetyInspector(Minion):
	Class, race, name = "Neutral", "", "Safety Inspector"
	mana, attack, health = 1, 1, 3
	index = "Darkmoon~Neutral~Minion~1~1~3~None~Safety Inspector~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Shuffle the lowest-Cost card from your hand into your deck. Draw a card"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Safety Inspector's battlecry shuffles the lowest-Cost card in player's hand into the deck and let player draw a card")
		curGame = self.Game
		ownHand = curGame.Hand_Deck.hands[self.ID]
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				cards, lowestCost = [], np.inf
				for i, card in enumerate(ownHand):
					if card.mana < lowestCost:
						cards, lowestCost = [i], card.mana
					elif card.mana == lowestCost:
						cards.append(i)
				i = npchoice(cards) if cards else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				card = ownHand[i]
				for trig in card.trigsBoard + card.trigsHand + card.trigsDeck:
					trig.disconnect()
				inOrigDeck = card.inOrigDeck
				card.__init__(curGame, self.ID)
				card.inOrigDeck = inOrigDeck
				curGame.Hand_Deck.shuffleCardintoDeck(card, self,ID)
		#Assume that player draws even if no card is shuffled
		curGame.Hand_Deck.drawCard(self.ID)
		return None
		
		
"""Mana 2 cards"""
class CostumedEntertainer(Minion):
	Class, race, name = "Neutral", "", "Costumed Entertainer"
	mana, attack, health = 2, 1, 2
	index = "Darkmoon~Neutral~Minion~2~1~2~None~Costumed Entertainer~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Give a random minion in your hand +2/+2"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		ownHand = curGame.Hand_Deck.hands[self.ID]
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(ownHand) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				PRINT(curGame, "Costumed Entertainer's battlecry gives a random minion in players hand +2/+2")
				ownHand[i].buffDebuff(2, 2)
		return None
		
		
class HorrendousGrowth(Minion):
	Class, race, name = "Neutral", "", "Horrendous Growth"
	mana, attack, health = 2, 2, 2
	index = "Darkmoon~Neutral~Minion~2~2~2~None~Horrendous Growth"
	requireTarget, keyWord, description = False, "", "Corrupt: Gain +1/+1. Can be Corrupted endlessly"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, HorrendousGrowth_Corrupted_3)] #只有在手牌中才会升级
		
class HorrendousGrowth_Corrupted_Mutable_3(Minion):
	Class, race, name = "Neutral", "", "Horrendous Growth"
	mana, attack, health = 2, 2, 2
	index = "Darkmoon~Neutral~Minion~2~2~2~None~Horrendous Growth~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "", "Corrupt: Gain +1/+1. Can be Corrupted endlessly"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_EndlessCorrupt(self)] #只有在手牌中才会升级
		
class Trig_EndlessCorrupt(TrigHand):
	def __init__(self, entity, corruptedType):
		self.blank_init(entity, ["ManaPaid"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand and ID == self.entity.ID and number > self.entity.mana
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		card = self.entity
		stat = int(type(card).__name__.split('_')[2])
		newIndex = "Darkmoon~Neutral~2~%d~%d~Minion~None~Horrendous Growth~Corrupted~Uncollectible"%(stat, stat)
		subclass = type("HorrendousGrowth_Corrupted_Mutable_"+str(stat), (HorrendousGrowth_Corrupted_Mutable_3, ),
						{"attack": stat, "health": stat, "index": newIndex}
						)
		self.Game.cardPool[newIndex] = subclass
		#The buffs on the cards carry over
		newCard = subclass(card.Game, card.ID)
		#Buff and mana effects, etc, will be preserved
		#Buff to cards in hand will always be permanent or temporary, not from Auras
		#Temporary attack changes on minions are NOT included in attack_Enchant
		attBuff, healthBuff = card.attack_Enchant - card.attack_0, card.health_Enchant - card.health_0
		newCard.buffDebuff(attBuff, healthBuff)
		for attGain, attRevertTime in card.tempAttChanges:
			newCard.buffDebuff(attGain, 0, attRevertTime)
		#Find keywords the new card doesn't have
		keyWords = newCard.keyWords.keys()
		#Since the Horrendous Growth has no predefined keywords, it can simply copy the predecessors
		newCard.keyWords, newCard.marks = copy.deepcopy(card.keyWords), copy.deepcopy(card.marks)
		newCard.trigsHand += [trig for trig in card.trigsHand if not isinstance(trig, Trig_Corrupt)]
		#There are no Corrupted cards with predefined Deathrattles
		newCard.deathrattles = [type(deathrattle)(newCard) for deathrattle in card.deathrattles]
		#Mana modifications
		newCard.manaMods = [manaMod.selfCopy(newCard) for manaMod in card.manaMods]
		
		card.Game.Hand_Deck.replaceCardinHand(card, newCard)
		
		
class ParadeLeader(Minion):
	Class, race, name = "Neutral", "", "Parade Leader"
	mana, attack, health = 2, 2, 2
	index = "Darkmoon~Neutral~Minion~2~2~2~None~Parade Leader"
	requireTarget, keyWord, description = False, "", "After you summon a Rush minion, give it +2 Attack"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_ParadeLeader(self)] #只有在手牌中才会升级
		
class Trig_ParadeLeader:
	def __init__(self, entity):
		self.blank_init(entity, ["MinionBeenSummoned"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject != self.entity and subject.ID == self.entity.ID and subject.keyWords["Rush"] > 0
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "After player summons Rush minion %s, Parade Leader gives it +2 Attack"%subject.name)
		subject.buffDebuff(2, 0)
		
		
class PrizeVendor(Minion):
	Class, race, name = "Neutral", "Murloc", "Prize Vendor"
	mana, attack, health = 2, 2, 3
	index = "Darkmoon~Neutral~Minion~2~2~3~Murloc~Prize Vendor~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Both players draw a card"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Prize Vendor's battlecry lets both players draw a card")
		self.Game.Hand_Deck.drawCard(self.ID)
		self.Game.Hand_Deck.drawCard(3-self.ID)
		return None
		
		
class RockRager(Minion):
	Class, race, name = "Neutral", "Elemental", "Rock Rager"
	mana, attack, health = 2, 5, 1
	index = "Darkmoon~Neutral~Minion~2~5~1~Elemental~Rock Rager~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt"
	
	
class Showstopper(Minion):
	Class, race, name = "Neutral", "", "Showstopper"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Neutral~Minion~2~3~2~None~Showstopper~Deathrattle"
	requireTarget, keyWord, description = False, "Deathrattle", "Deathrattle: Silence all minions"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [SilenceAllMinions(self)]
		
class SilenceAllMinions(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "Deathrattle: Silence all minions triggers")
		for minion in curGame.minionsonBoard(1) + curGame.minionsonBoard(2):
			minion.getsSilenced()
			
			
class WrigglingHorror(Minion):
	Class, race, name = "Neutral", "", "Wriggling Horror"
	mana, attack, health = 2, 2, 1
	index = "Darkmoon~Neutral~Minion~2~2~1~None~Wriggling Horror~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Give adjacent minions +1/+1"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.onBoard:
			PRINT(self.Game, "Wriggling Horror's battlecry gives adjacent minions +1/+1")
			for minion in self.Game.neighbors2(self)[0]:
				minion.buffDebuff(1, 1)
		return None
		
		
"""Mana 3 cards"""
class BananaVendor(Minion):
	Class, race, name = "Neutral", "", "Banana Vendor"
	mana, attack, health = 3, 2, 4
	index = "Darkmoon~Neutral~Minion~3~2~4~None~Banana Vendor~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Add 2 Bananas to each player's hand"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Banana Vendor's battlecry adds 2 Bananas to each player's hand")
		self.Game.Hand_Deck.addCardtoHand([Bananas_Darkmoon, Bananas_Darkmoon], self.ID, "type")
		self.Game.Hand_Deck.addCardtoHand([Bananas_Darkmoon, Bananas_Darkmoon], 3-self.ID, "type")
		return None
		
class Bananas_Darkmoon(Spell):
	Class, name = "Neutral", "Bananas"
	requireTarget, mana = True, 1
	index = "Darkmoon~Neutral~Spell~1~Bananas~Uncollectible"
	description = "Give a minion +1/+1"
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Bananas is cast and gives minion %s +1/+1."%target.name)
			target.buffDebuff(1, 1)
		return target
		
		
class DarkmoonDirigible(Minion):
	Class, race, name = "Neutral", "Mech", "Darkmoon Dirigible"
	mana, attack, health = 3, 3, 2
	index = "Darkmoon~Neutral~Minion~3~3~2~Mech~Darkmoon Dirigible~Divine Shield"
	requireTarget, keyWord, description = False, "Divine Shield", "Divine Shield. Corrupt: Gain Rush"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, DarkmoonDirigible_Corrupted)] #只有在手牌中才会升级
		
class DarkmoonDirigible_Corrupted(Minion):
	Class, race, name = "Paladin", "Mech", "Darkmoon Dirigible"
	mana, attack, health = 3, 3, 2
	index = "Darkmoon~Neutral~Minion~3~3~2~Mech~Darkmoon Dirigible~Divine Shield~Rush~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Divine Shield,Rush", "Corrupted. Divine Shield, Rush"
	
	
class DarkmoonStatue(Minion):
	Class, race, name = "Neutral", "", "Darkmoon Statue"
	mana, attack, health = 3, 0, 5
	index = "Darkmoon~Neutral~Minion~3~0~5~None~Darkmoon Statue"
	requireTarget, keyWord, description = False, "", "Your other minions have +1 Attack. Corrupt: This gains +4 Attack"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, DarkmoonStatue_Corrupted)] #只有在手牌中才会升级
		self.auras["Buff Aura"] = BuffAura_Dealer_All(self, 1, 0)
		
class DarkmoonStatue_Corrupted(Minion):
	Class, race, name = "Paladin", "", "Darkmoon Statue"
	mana, attack, health = 3, 4, 5
	index = "Darkmoon~Neutral~Minion~3~4~5~None~Darkmoon Statue~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "", "Corrupted. Your other minions have +1 Attack"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.auras["Buff Aura"] = BuffAura_Dealer_All(self, 1, 0)
		
		
class Gyreworm(Minion):
	Class, race, name = "Neutral", "Elemental", "Gyreworm"
	mana, attack, health = 3, 3, 2
	index = "Darkmoon~Neutral~Minion~3~3~2~Elemental~Gyreworm~Battlecry"
	requireTarget, keyWord, description = True, "", "Battlecry: If you played an Elemental last turn, deal 3 damage"
	def returnTrue(self, choice=0):
		return self.Game.Counters.numElementalsPlayedLastTurn[self.ID] > 0
		
	def effectCanTrigger(self):
		self.effectViable = self.Game.Counters.numElementalsPlayedLastTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target and self.Game.Counters.numElementalsPlayedLastTurn[self.ID] > 0:
			PRINT(self.Game, "Gyreworm's battlecry deals 3 damage to %s"%target.name)
			self.dealsDamage(target, 3)
		return target
		
		
class InconspicuousRider(Minion):
	Class, race, name = "Neutral", "", "Inconspicuous Rider"
	mana, attack, health = 3, 2, 2
	index = "Darkmoon~Neutral~Minion~3~2~2~None~Inconspicuous Rider~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Cast a Secret from your deck"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(curGame, "Inconspicuous Rider's casts a Secret from player's deck")
		self.Game.Secrets.deploySecretsfromDeck(self.ID)
		return None
		
		
class KthirRitualist(Minion):
	Class, race, name = "Neutral", "", "K'thir Ritualist"
	mana, attack, health = 3, 4, 4
	index = "Darkmoon~Neutral~Minion~3~4~4~None~K'thir Ritualist~Taunt~Battlecry"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Battlecry: Add a random 4-Cost minion to your opponent's hand"
	poolIdentifier = "4-Cost Minions"
	@classmethod
	def generatePool(cls, Game):
		return "4-Cost Minions", list(Game.MinionsofCost[4].values())
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "K'thir Ritualist's battlecry adds a random 4-Cost minion tp the opponent's hand")
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				minion = npchoice(curGame.RNGPools["4-Cost Minions"])
				curGame.fixedGuides.append(minion)
			curGame.Hand_Deck.addCardtoHand(minion, 3-self.ID, "type")
		return None
		
"""Mana 4 cards"""
class CircusAmalgam(Minion):
	Class, race, name = "Neutral", "Elemental,Mech,Demon,Murloc,Dragon,Beast,Pirate,Totem", "Circus Amalgam"
	mana, attack, health = 4, 4, 5
	index = "Darkmoon~Neutral~Minion~4~4~5~Elemental,Mech,Demon,Murloc,Dragon,Beast,Pirate,Totem~Circus Amalgam~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. This has all minion types"
	
	
class CircusMedic(Minion):
	Class, race, name = "Neutral", "", "Circus Medic"
	mana, attack, health = 4, 3, 4
	index = "Darkmoon~Neutral~Minion~4~3~4~None~Circus Medic~Battlecry"
	requireTarget, keyWord, description = True, "", "Battlecry: Restore 4 Health. Corrupt: Deal 4 damage instead"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, CircusMedic_Corrupted)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			heal = 4 * (2 ** self.countHealDouble())
			PRINT(self.Game, "Circus Medic's battlecry restores %d health to %s"%(heal, target.name))
			self.restoresHealth(target, heal)
		return target
		
class CircusMedic_Corrupted(Minion):
	Class, race, name = "Neutral", "", "Circus Medic"
	mana, attack, health = 4, 3, 4
	index = "Darkmoon~Neutral~Minion~4~3~4~None~Circus Medic~Battlecry~Corrupted~Uncollectible"
	requireTarget, keyWord, description = True, "", "Corrupted. Battlecry: Deal 4 damage"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Circus Medic's battlecry deals 4 damage to %s"%target.name)
			self.dealsDamage(target, 4)
		return target
		
		
class FantasticFirebird(Minion):
	Class, race, name = "Neutral", "Elemental", "Fantastic Firebird"
	mana, attack, health = 4, 3, 5
	index = "Darkmoon~Neutral~Minion~4~3~5~Elemental~Fantastic Firebird~Windfury"
	requireTarget, keyWord, description = False, "Windfury", "Windfury"
	
	
class KnifeVendor(Minion):
	Class, race, name = "Neutral", "", "Knife Vendor"
	mana, attack, health = 4, 3, 4
	index = "Darkmoon~Neutral~Minion~4~3~4~None~Knife Vendor~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Deal 4 damage to each hero"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Knife Vendor's battlecry deals 4 damage to each player")
		self.dealsAOE([self.Game.heroes[1], self.Game.heroes[2]], [4, 4])
		return None
		
"""Mana 5 cards"""
class DerailedCoaster(Minion):
	Class, race, name = "Neutral", "", "Derailed Coaster"
	mana, attack, health = 5, 3, 2
	index = "Darkmoon~Neutral~Minion~5~3~2~None~Derailed Coaster~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Summon a 1/1 Rider with Rush for each minion in your hand"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Derailed Coaster's battlecry summons a 1/1 Rider with Rush for each minion in player's hand")
		num = sum(card.type == "Minion" for card in curGame.Hand_Deck.hands[self.ID])
		if num: curGame.summon([Rider(curGame, self.ID) for i in range(num)], (self.position, "totheRight"), self.ID)
		return None
		
class (Minion):
	Class, race, name = "Neutral", "", "Rider"
	mana, attack, health = 1, 1, 1
	index = "Darkmoon~Neutral~Minion~1~1~1~None~Rider~Rush~Uncollectible"
	requireTarget, keyWord, description = False, "Rush", "Rush"
	
#Assume corrupted card don't inherit any buff/debuff
#Assume transformation happens when card is played
class FleethoofPearltusk(Minion):
	Class, race, name = "Neutral", "Beast", "Fleethoof Pearltusk"
	mana, attack, health = 5, 4, 4
	index = "Darkmoon~Neutral~Minion~5~4~4~Beast~Fleethoof Pearltusk~Rush"
	requireTarget, keyWord, description = False, "Rush", "Rush. Corrupt: Gain +4/+4"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, FleethoofPearltusk_Corrupted)] #只有在手牌中才会升级
		
class FleethoofPearltusk_Corrupted(Minion):
	Class, race, name = "Neutral", "Beast", "Fleethoof Pearltusk"
	mana, attack, health = 5, 8, 8
	index = "Darkmoon~Neutral~Minion~5~8~8~Beast~Fleethoof Pearltusk~Rush~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Rush", "Rush"
	
	
class OptimisticOgre(Minion):
	Class, race, name = "Neutral", "", "Optimistic Ogre"
	mana, attack, health = 5, 6, 7
	index = "Darkmoon~Neutral~5~6~7~Minion~None~Optimistic Ogre"
	requireTarget, keyWord, description = False, "", "50% chance to attack the correct enemy"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.triggersonBoard = [Trigger_OptimisticOgre(self)]
		
class Trigger_OptimisticOgre(TriggeronBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAttacksMinion", "MinionAttacksHero", "BattleFinished"])
		self.trigedThisBattle = False
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		#The trigger can be reset any time by "BattleFinished".
		#Otherwise, can only trigger if there are enemies other than the target.
		#游荡怪物配合误导可能会将对英雄的攻击目标先改成对召唤的随从，然后再发回敌方英雄，说明攻击一个错误的敌人应该也是游戏现记录的目标之外的角色。
		return not signal.startswith("Minion") or (subject == self.entity and self.entity.onBoard and target[1] and not self.trigedThisBattle \
													and self.entity.Game.charsAlive(3-subject.ID, target[1]) \
													)
													
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.entity.onBoard:
			if signal == "BattleFinished": #Reset the Forgetful for next battle event.
				self.trigedThisBattle = False
			elif target: #Attack signal
				curGame, side = self.entity.Game, 3- self.entity.ID
				if curGame.mode == 0:
					char, redirect = None, 0
					if curGame.guides:
						i, where, redirect = curGame.guides.pop(0)
						if char = curGame.find(i, where)
					else:
						otherEnemies = curGame.charsAlive(side, target[1])
						if otherEnemies:
							char, redirect = npchoice(otherEnemies), nprandint(2)
							curGame.fixedGuides.append((char.position, char.type+str(char.ID), redirect))
						else:
							curGame.fixedGuides.append((0, '', 0))
					if char and redirect: #Redirect is 0/1, indicating whether the attack will redirect or not
						#玩家命令的一次攻击中只能有一次触发机会。只要满足进入50%判定的条件，即使没有最终生效，也不能再次触发。
						target[1], self.trigedThisBattle = char, True
						
"""Mana 6 cards"""
class ClawMachine(Minion):
	Class, race, name = "Neutral", "Mech", "Claw Machine"
	mana, attack, health = 6, 6, 3
	index = "Darkmoon~Neutral~Minion~6~6~3~Mech~Claw Machine~Rush~Deathrattle"
	requireTarget, keyWord, description = False, "Rush", "Rush. Deathrattle: Draw a minion and give it +3/+3"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [DrawaMinion_GiveitPlus3Plus3(self)]
		
class DrawaMinion_GiveitPlus3Plus3(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "Deathrattle: Draw a minion and give it +3/+3 triggers")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.entity.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.Hand_Deck.drawCard(self.entity.ID, i)[0]
				if minion: minion.buffDebuff(3, 3)
				
				
"""Mana 7 cards"""
class SilasDarkmoon(Minion):
	Class, race, name = "Neutral", "", "Silas Darkmoon"
	mana, attack, health = 7, 4, 4
	index = "Darkmoon~Neutral~Minion~7~4~4~None~Silas Darkmoon~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Choose a direction to rotate all minions"
	
class Strongman(Minion):
	Class, race, name = "Neutral", "", "Strongman"
	mana, attack, health = 7, 6, 6
	index = "Darkmoon~Neutral~Minion~7~6~6~None~Strongman~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Corrupt: This costs (0)"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, Strongman_Corrupt)] #只有在手牌中才会升级
		
class Strongman_Corrupt(Minion):
	Class, race, name = "Neutral", "", "Strongman"
	mana, attack, health = 0, 6, 6
	index = "Darkmoon~Neutral~Minion~0~6~6~None~Strongman~Taunt~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Corrupted. Taunt"
	
	
"""Mana 9 cards"""
class CarnivalClown(Minion):
	Class, race, name = "Neutral", "", "Carnival Clown"
	mana, attack, health = 9, 4, 4
	index = "Darkmoon~Neutral~Minion~9~4~4~None~Carnival Clown~Taunt~Battlecry"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Battlecry: Summon 2 copies of this. Corrupted: Fill your board with copies"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, CarnivalClown_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		#假设已经死亡时不会召唤复制
		if self.onBoard or self.inDeck:
			PRINT(self.Game, "Carnival Clown's battlecry summons 2 copies of the minion")
			copies = [self.selfCopy(self.ID) for i in range(2)]
			pos = (self.position, "leftandRight") if self.onBoard else (-1, "totheRightEnd")
			self.Game.summon(copies, pos, self.ID)
		return None
		
class CarnivalClown_Corrupt(Minion):
	Class, race, name = "Neutral", "", "Carnival Clown"
	mana, attack, health = 9, 4, 4
	index = "Darkmoon~Neutral~Minion~9~4~4~None~Carnival Clown~Taunt~Battlecry~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Corrupted. Taunt. Battlecry: Fill your board with copies of this"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		#假设已经死亡时不会召唤复制
		PRINT(self.Game, "Carnival Clown's battlecry fills the board with copies of the minion")
		if self.onBoard:
			copies = [self.selfCopy(self.ID) for i in range(6)]
			self.Game.summon(copies, (self.position, "leftandRight"), self.ID)
		else:
			copies = [self.selfCopy(self.ID) for i in range(7)]
			self.Game.summon(copies, (-1, "totheRightEnd"), self.ID)
		return None
		
"""Mana 10 cards"""
#Assume one can get CThun as long as pieces are played, even if it didn't start in their deck
class Trig_CThun:
	def __init__(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.temp = False
		self.piece = []
		
	def connect(self):
		try: self.Game.trigsBoard[self.ID]["CThunPiece"].append(self)
		except: self.Game.trigsBoard[self.ID]["CThunPiece"] = [self]
		
	def disconnect(self):
		try: self.Game.trigsBoard[self.ID]["CThunPiece"].remove(self)
		except: pass
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.ID and subject == self.spellDiscovered
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			if self.Game.GUI: self.Game.GUI.showOffBoardTrig(CThuntheShattered(self.Game, self.ID), linger=False)
			self.effect(signal, ID, subject, target, number, comment)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		if ID == self.ID and number not in self.pieces:
			self.pieces.append(number)
			if len(self.pieces) > 3:
				PRINT("Player %d's C'Thun is completed and shuffles into the deck"%ID)
				self.Game.Hand_Deck.shuffleCardintoDeck(CThuntheShattered(self.Game, ID), ID)
				self.disconnect()
				
	def createCopy(self, game): #不是纯的只在回合结束时触发，需要完整的createCopy
		if self not in game.copiedObjs: #这个扳机没有被复制过
			trigCopy = type(self)(game, self.ID)
			trigCopy.pieces = [i for i in self.pieces]
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
class BodyofCThun(Spell):
	Class, name = "Neutral", "Body of C'Thun"
	requireTarget, mana = False, 5
	index = "Darkmoon~Neutral~Spell~5~Body of C'Thun~Uncollectible"
	description = "Summon a 6/6 C'Thun's body with Taunt"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Body of C'Thun summons a 6/6 Body of C'Thun")
		self.Game.summon(BodyofCThun(self.Game, self.ID), -1, self.ID)
		#Assume the spell effect will increase the counter
		if "CThunPiece" not in self.Game.trigsBoard[self.ID]:
			Trig_CThun.connect()
		self.Game.sendSignal("CThunPiece", self.ID, None, None, 1, "")
		return None
		
class BodyofCThun_Minion(Minion):
	Class, race, name = "Neutral", "", "Body of C'Thun"
	mana, attack, health = 6, 6, 6
	index = "Darkmoon~Neutral~Minion~6~6~6~None~Body of C'Thun~Taunt~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Taunt"
	
class EyeofCThun(Spell):
	Class, name = "Neutral", "Eye of C'Thun"
	requireTarget, mana = False, 5
	index = "Darkmoon~Neutral~Spell~5~Eye of C'Thun~Uncollectible"
	description = "Deal 7 damage randomly split among all enemies"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		damage = (7 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
		side, curGame = 3 - self.ID, self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Eye of C'Thun deals %d damage randomly split among enemies."%damage)
			for num in range(damage):
				char = None
				if curGame.guides:
					i, where = curGame.guides.pop(0)
					if where: char = curGame.find(i, where)
				else:
					objs = curGame.charsAlive(side)
					if objs:
						char = npchoice(objs)
						curGame.fixedGuides.append((side, "hero") if char.type == "Hero" else (char.position, "minion%d"%side))
					else:
						curGame.fixedGuides.append((0, ''))
				if char:
					self.dealsDamage(char, 1)
				else: break
		if "CThunPiece" not in self.Game.trigsBoard[self.ID]:
			Trig_CThun.connect()
		self.Game.sendSignal("CThunPiece", self.ID, None, None, 2, "")
		return None
		
class HeartofCThun(Spell):
	Class, name = "Neutral", "Heart of C'Thun"
	requireTarget, mana = False, 5
	index = "Darkmoon~Neutral~Spell~5~Heart of C'Thun~Uncollectible"
	description = "Deal 3 damage to all minions"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		damage = (3 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
		targets = self.Game.minionsonBoard(1) + self.Game.minionsonBoard(2)
		PRINT(self.Game, "Heart of C'Thun deals %d damage to all minions."%damage)
		self.dealsAOE(targets, [damage] * len(targets))
		if "CThunPiece" not in self.Game.trigsBoard[self.ID]:
			Trig_CThun.connect()
		self.Game.sendSignal("CThunPiece", self.ID, None, None, 3, "")
		return None
		
class MawofCThun(Spell):
	Class, name = "Neutral", "Maw of C'Thun"
	requireTarget, mana = False, 5
	index = "Darkmoon~Neutral~Spell~5~Maw of C'Thun~Uncollectible"
	description = "Destroy a minion"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Maw of C'Thun destroys minion %s"%target.name)
			self.Game.killMinion(self, target)
		#Assume the counter still works even if there is no target designated
		if "CThunPiece" not in self.Game.trigsBoard[self.ID]:
			Trig_CThun.connect()
		self.Game.sendSignal("CThunPiece", self.ID, None, None, 4, "")
		return None
		
class CThuntheShattered(Minion):
	Class, race, name = "Neutral", "", "C'Thun, the Shattered"
	mana, attack, health = 10, 6, 6
	index = "Darkmoon~Neutral~Minion~10~6~6~None~C'Thun, the Shattered~Battlecry~Start of Game~Legendary"
	requireTarget, keyWord, description = False, "", "Start of Game: Break into pieces. Battlecry: Deal 30 damage randomly split among all enemies"
	
	def startofGame(self):
		#Remove the card from deck. Assume the final card WON't count as deck original card 
		curGame, ID = self.Game, self.ID
		curGame.Hand_Deck.extractfromDeck(self, ID=0, all=False, enemyCanSee=True)
		curGame.Hand_Deck.shuffleCardintoDeck([BodyofCThun(curGame, ID), EyeofCThun(curGame, ID), HeartofCThun(curGame ID), MawofCThun(curGame, ID)], ID)
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		side, curGame = 3-self.ID, self.Game
		if curGame.mode == 0:
			PRINT(curGame, "C'Thun, the Shattered's battlecry deals 30 damage randomly split among all enemies")
			for num in range(30):
				char = None
				if curGame.guides:
					i, where = curGame.guides.pop(0)
					if where: char = curGame.find(i, where)
				else:
					objs = curGame.charsAlive(side)
					if objs:
						char = npchoice(objs)
						curGame.fixedGuides.append((side, "hero") if char.type == "Hero" else (char.position, "minion%d"%side))
					else:
						curGame.fixedGuides.append((0, ''))
				if char:
					self.dealsDamage(char, 1)
				else: break
		return None
		
		
class DarkmoonRabbit(Minion):
	Class, race, name = "Neutral", "Beast", "Darkmoon Rabbit"
	mana, attack, health = 10, 1, 1
	index = "Darkmoon~Neutral~Minion~10~1~1~Beast~Darkmoon Rabbit~Rush~Poisonous"
	requireTarget, keyWord, description = False, "Rush,Poisonous", "Rush, Poisonous. Also damages the minions next to whomever this attacks"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.marks["Sweep"] = 1
		
		
class NZothGodoftheDeep(Minion):
	Class, race, name = "Neutral", "", "N'Zoth, God of the Deep"
	mana, attack, health = 10, 5, 7
	index = "Darkmoon~Neutral~Minion~10~5~7~None~N'Zoth, God of the Deep~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Resurrect a friendly minion of each minion type"
	#The mana effect should be carried by each card, since card copied to opponent should also cost (0).
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame, ID = self.Game, self.ID
		if curGame.mode == 0:
			if curGame.guides:
				minions = curGame.guides.pop(0)
			else: #First, categorize. Second, from each type, select one.
				minions, pool = [], curGame.Counters.minionsDiedThisGame[ID]
				types = {"Beast": [], "Pirate": [], "Elemental": [], "Mech": [], "Dragon": [], "Totem": [], "Demon": [], "Murloc": []}
				for minion in pool:
					race = minion.index.split('~')[6]
					if race != "None": #Has single race
						if len(race) < 10: types[race].append(minion.index)
						else:
							for s in race.split(','): types[s].append(minion.index)
				for race in types.keys():
					minions += npchoice(cards, min(1, len(types[race])), replace=False)
				minions = tuple([curGame.cardPool[index] for index in cards])
				curGame.fixedGuides.append(cards) #Can be empty, and the empty tuple will simply add nothing to hand
			PRINT(curGame, "N'Zoth, God of the Deep's battlecry adds a copy of each corrupted card player played this game. And they cost (0) this turn")
			if cards:
				cards = [card(curGame, ID) for card in cards]
				curGame.Hand_Deck.addCardtoHand(cards, ID)
				for card in cards:
					Cost0ThisTurn(card).applies()
		return None
		
class CurseofFlesh(Spell):
	Class, name = "Neutral", "Curse of Flesh"
	requireTarget, mana = False, 0
	index = "Darkmoon~Neutral~Spell~0~Curse of Flesh~Uncollectible"
	description = "Fill the board with random minions, then give your Rush"
	
class DevouringHunger(Spell):
	Class, name = "Neutral", "Devouring Hunger"
	requireTarget, mana = False, 0
	index = "Darkmoon~Neutral~Spell~0~Devouring Hunger~Uncollectible"
	description = "Destroy all other minions. Gain their Attack and Health"
	
class HandofFate(Spell):
	Class, name = "Neutral", "Hand of Fate"
	requireTarget, mana = False, 0
	index = "Darkmoon~Neutral~Spell~0~Hand of Fate~Uncollectible"
	description = "Fill your hand with random spells. They cost (0) this turn"
	
class MindflayerGoggles(Spell):
	Class, name = "Neutral", "Mindflayer Goggles"
	requireTarget, mana = False, 0
	index = "Darkmoon~Neutral~Spell~0~Mindflayer Goggles~Uncollectible"
	description = "Take control of three random enemy minions"
	
class Mysterybox(Spell):
	Class, name = "Neutral", "Mysterybox"
	requireTarget, mana = False, 0
	index = "Darkmoon~Neutral~Spell~0~Mysterybox~Uncollectible"
	description = "Cast a random spell for each spell you've cast this game(targets chosen randomly)"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(curGame, "Rod of Roasting casts 'Pyroblast' randomly until a player dies")
		while True:
			minions = curGame.minionsAlive(1) + curGame.minionsAlive(2)
			heroes = [hero for hero in curGame.heroes.values() if hero.health > 0 and not hero.dead]
			#Stop if not both players are alive, or (players are alive but there are no living minions and players are immune)
			#In principle, if both players have Immune or Blur effect, this shouldn't go into an infinite loop. But Blur is rare
			if len(heroes) < 2 or (not minions and curGame.status[1]["Immune"] and curGame.status[2]["Immune"]):
				break
			Pyroblast(curGame, self.ID).cast()
		return None
		
class RodofRoasting(Spell):
	Class, name = "Neutral", "Rod of Roasting"
	requireTarget, mana = False, 0
	index = "Darkmoon~Neutral~Spell~0~Rod of Roasting~Uncollectible"
	description = "Cast 'Pyroblast' randomly until a player dies"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(curGame, "Rod of Roasting casts 'Pyroblast' randomly until a player dies")
		while True:
			minions = curGame.minionsAlive(1) + curGame.minionsAlive(2)
			heroes = [hero for hero in curGame.heroes.values() if hero.health > 0 and not hero.dead]
			#Stop if not both players are alive, or (players are alive but there are no living minions and players are immune)
			#In principle, if both players have Immune or Blur effect, this shouldn't go into an infinite loop. But Blur is rare
			if len(heroes) < 2 or (not minions and curGame.status[1]["Immune"] and curGame.status[2]["Immune"]):
				break
			Pyroblast(curGame, self.ID).cast()
		return None
		
class YoggSaronMasterofFate(Minion):
	Class, race, name = "Neutral", "", "Yogg-Saron, Master of Fate"
	mana, attack, health = 10, 7, 5
	index = "Darkmoon~Neutral~Minion~10~7~5~None~Yogg-Saron, Master of Fate~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: If you've cast 10 spells this game, spin the Wheel of Yogg-Saron"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				wheel = curGame.guides.pop(0)
			else:
				if sum("~Spell~" in index for index in curGame.Counters.cardsPlayedThisGame[self.ID]) > 9:
					wheel = curGame.Counters.spellsonFriendliesThisGame[ID]
				cards = npchoice([], , replace=False)
				cards = tuple([curGame.cardPool[index] for index in cards])
				curGame.fixedGuides.append(cards) #Can be empty, and the empty tuple will simply add nothing to hand
			PRINT(curGame, "Y'Shaarj, the Defiler's battlecry adds a copy of each corrupted card player played this game. And they cost (0) this turn")
			if cards:
				cards = [card(curGame, ID) for card in cards]
				curGame.Hand_Deck.addCardtoHand(cards, ID)
				for card in cards:
					Cost0ThisTurn(card).applies()
		return None
		
class YShaarjtheDefiler(Minion):
	Class, race, name = "Neutral", "", "Y'Shaarj, the Defiler"
	mana, attack, health = 10, 10, 10
	index = "Darkmoon~Neutral~Minion~10~10~10~None~Y'Shaarj, the Defiler~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Add a copy of each Corrupted card you've played this game to your hand. They cost (0) this turn"
	#The mana effect should be carried by each card, since card copied to opponent should also cost (0).
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame, ID = self.Game, self.ID
		if curGame.mode == 0:
			if curGame.guides:
				cards = curGame.guides.pop(0)
			else:
				cards = curGame.Counters.spellsonFriendliesThisGame[ID]
				cards = npchoice(cards, min(curGame.Hand_Deck.spaceinHand(ID), len(cards)), replace=False)
				cards = tuple([curGame.cardPool[index] for index in cards])
				curGame.fixedGuides.append(cards) #Can be empty, and the empty tuple will simply add nothing to hand
			PRINT(curGame, "Y'Shaarj, the Defiler's battlecry adds a copy of each corrupted card player played this game. And they cost (0) this turn")
			if cards:
				cards = [card(curGame, ID) for card in cards]
				curGame.Hand_Deck.addCardtoHand(cards, ID)
				for card in cards:
					Cost0ThisTurn(card).applies()
		return None
		
class Cost0ThisTurn:
	def __init__(self, card):
		self.card = card
		#Don't need changeby and changedto or lowerBound
		self.source = None
		
	def handleMana(self):
		self.card.mana = 0
		
	def applies(self):
		card = self.card
		card.manaMods.append(self)
		if card in card.Game.Hand_Deck.hands[card.ID]:
			try: card.Game.trigsBoard[card.ID]["TurnEnds"].append(self)
			except: card.Game.trigsBoard[card.ID]["TurnEnds"] = [self]
			card.Game.Manas.calcMana_Single(card)
			
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.card.inHand
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		self.getsRemoved()
		self.card.Game.Manas.calcMana_Single(self.card)
		
	def getsRemoved(self):
		try: self.card.Game.trigsBoard[self.card.ID]["TurnEnds"].remove(self)
		except: pass
		try: self.card.manaMods.remove(self)
		except: pass
		
	def selfCopy(self, recipient):
		return Cost0ThisTurn(recipient)
		
		
"""Demon Hunter cards"""
class FelscreamBlast(Spell):
	Class, name = "Demon Hunter", "Felscream Blast"
	requireTarget, mana = True, 1
	index = "Darkmoon~Demon Hunter~Spell~1~Felscream Blast~Lifesteal"
	description = "Lifesteal. Deal 1 damage to a minion and its neighbors"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.keyWords["Lifesteal"] = 1
		
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			damage = (1 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Felscream Blast deals %d damage to %s and its neighbors."%(damage, target.name))
			neighbors = self.Game.neighbors2(target)[0]
			if target.onBoard and neighbors:
				self.dealsAOE([target] + neighbors, [damage] * (1 + len(neighbors)))
			else:
				self.dealsDamage(target, damage)
		return target
		
		
class ThrowGlaive(Minion):
	Class, name = "Demon Hunter", "Throw Glaive"
	requireTarget, mana = True, 1
	index = "Darkmoon~Demon Hunter~Spell~1~Throw Glaive"
	description = "Deal 2 damage to a minion. If it dies, add a temporary copy of this to your hand"
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			damage = (2 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Throw Glaive deals %d damage to minion %s"%(damage, target.name))
			dmgTaker, damageActual = self.dealsDamage(target, damage)
			if dmgTaker.health < 1 or dmgTaker.dead:
				PRINT(self.Game, "Throw Glaive kills the target and adds a temporary copy of Throw Glaive to player's hand.")
				card = ThrowGlaive(self.Game, self.ID)
				card.trigsHand = [Trig_Echo(card)]
				self.Game.Hand_Deck.addCardtoHand(card, self.ID)
		return target
		
		
class RedeemedPariah(Minion):
	Class, race, name = "Demon Hunter", "", "Redeemed Pariah"
	mana, attack, health = 2, 2, 3
	index = "Darkmoon~Demon Hunter~Minion~2~2~3~None~Redeemed Pariah"
	requireTarget, keyWord, description = False, "", "After you play an Outcast card, gain +1/+1"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_RedeemedPariah(self)]
		
class Trig_RedeemedPariah(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionBeenPlayed", "SpellBeenPlayed", "WeaponBeenPlayed", "HeroCardBeenPlayed"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject.ID == self.entity.ID and "~Outcast" in subject.index
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "Player plays an Outcast card and Redeemed Pariah gains +1/+1.")
		self.entity.buffDebuff(1, 1)
		
		
class Acrobatics(Spell):
	Class, name = "Demon Hunter", "Acrobatics"
	requireTarget, mana = False, 3
	index = "Darkmoon~Demon Hunter~Spell~3~Acrobatics"
	description = "Draw 2 cards. If you play both this turn, draw 2 more"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Stiltstepper's battlecry lets player draw a card and ")
		card1 = self.Game.Hand_Deck.drawCard(self.ID)[0]
		card2 = self.Game.Hand_Deck.drawCard(self.ID)[0]
		if card1 and card2: AcrobaticsEffect(self.Game, self.ID, [card1, card2]).connect()
		return None
		
class AcrobaticsEffect:
	def __init__(self, Game, ID, cardsDrawn):
		self.Game, self.ID = Game, ID
		self.temp = False
		#Assume the trig is after the card is played
		self.signals = ["MinionBeenPlayed", "SpellBeenPlayed", "WeaponBeenPlayed", "HeroCardBeenPlayed"]
		self.cardsDrawn = cardsDrawn
		
	def connect(self):
		for sig in self.signals:
			try: self.Game.trigsBoard[self.ID][sig].append(self)
			except: self.Game.trigsBoard[self.ID][sig] = [self]
		self.Game.turnEndTrigger.append(self)
		
	def disconnect(self):
		for sig in self.signals:
			try: self.Game.trigsBoard[self.ID][sig].remove(self)
			except: pass
		try: self.Game.turnEndTrigger.remove(self)
		except: pass
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.ID and subject in self.cardsDrawn
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			if self.Game.GUI: self.Game.GUI.showOffBoardTrig(AcrobaticsEffect(self.Game, self.ID), linger=False)
			self.effect(signal, ID, subject, target, number, comment)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.Game, "The drawn card is played and Stiltstepper's effect gives player +4 Attack this turn")
		try: self.cardsDrawn.remove(subject)
		except: pass
		if not self.cardsDrawn:
			PRINT(self.Game, "Both cards drawn by Acrobatics have been played. Play draws 2 cards")
			self.Game.Hand_Deck.drawCard(self.ID)
			self.Game.Hand_Deck.drawCard(self.ID)
		self.disconnect()
		
	def turnEndTrigger(self):
		self.disconnect()
		
	def createCopy(self, game): #不是纯的只在回合结束时触发，需要完整的createCopy
		if self not in game.copiedObjs: #这个扳机没有被复制过
			trigCopy = type(self)(game, self.ID)
			trigCopy.cardsDrawn = [card.createCopy(game) for card in self.cardsDrawn]
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
			
class DreadlordsBite(Weapon):
	Class, name, description = "Demon Hunter", "Dreadlord's Bite", "Outcast: Deal 1 damage to all enemies"
	mana, attack, durability = 3, 3, 2
	index = "Darkmoon~Demon Hunter~Weapon~3~3~2~Dreadlord's Bite~Outcast"
	
	def effectCanTrigger(self):
		self.effectViable = self.Game.Hand_Deck.outcastcanTrigger(self)
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if posinHand == 0 or posinHand == -1:
			PRINT(self.Game, "Dreadlord's Bite's Outcast triggers and deals 1 damage to all enemies")
			enemies = [self.Game.heroes[3-self.ID]] + self.Game.minionsonBoard(3-self.ID)
			self.dealsDamage(enemies, [1] * len(enemies))
		return None
		
		
class FelsteelExecutioner(Minion):
	Class, race, name = "Demon Hunter", "Elemental", "Felsteel Executioner"
	mana, attack, health = 3, 4, 3
	index = "Darkmoon~Demon Hunter~Minion~3~4~3~Elemental~Felsteel Executioner"
	requireTarget, keyWord, description = False, "", "Corrupt: Become a weapon"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, FelsteelExecutioner_Corrupt)] #只有在手牌中才会升级
		
class FelsteelExecutioner_Corrupt(Weapon):
	Class, name, description = "Demon Hunter", "Felsteel Executioner", "Corrupted"
	mana, attack, durability = 3, 4, 3
	index = "Darkmoon~Demon Hunter~Weapon~3~4~3~Felsteel Executioner~Corrupted~Uncollectible"
	
	
class LineHopper(Minion):
	Class, race, name = "Demon Hunter", "", "Line Hopper"
	mana, attack, health = 3, 3, 4
	index = "Darkmoon~Demon Hunter~Minion~3~3~4~None~Line Hopper"
	requireTarget, keyWord, description = False, "", "Your Outcast cards cost (1) less"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.auras["Mana Aura"] = ManaAura_Dealer(self, changeby=-1, changeto=-1)
		
	def manaAuraApplicable(self, subject): #ID用于判定是否是我方手中的随从
		return "~Outcast" in subject.index and subject.ID == self.ID
		
		
class InsatiableFelhound(Minion):
	Class, race, name = "Demon Hunter", "Demon", "Insatiable Felhound"
	mana, attack, health = 3, 2, 5
	index = "Darkmoon~Demon Hunter~Minion~3~2~5~Demon~Insatiable Felhound~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Corrupt: Gain +1/+1 and Lifesteal"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, InsatiableFelhound_Corrupt)] #只有在手牌中才会升级
		
class InsatiableFelhound_Corrupt(Minion):
	Class, race, name = "Demon Hunter", "Demon", "Insatiable Felhound"
	mana, attack, health = 3, 3, 6
	index = "Darkmoon~Demon Hunter~Minion~3~3~6~Demon~Insatiable Felhound~Taunt~Lifesteal~Corrupt~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt,Lifesteal", "Taunt, Lifesteal"
	
	
class RelentlessPersuit(Spell):
	Class, name = "Demon Hunter", "Relentless Persuit"
	requireTarget, mana = False, 3
	index = "Darkmoon~Demon Hunter~Spell~3~Relentless Persuit"
	description = "Give your hero +4 Attack and Immune this turn"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Relentless Persuit gives player +4 Attack and Immune this turn")
		self.Game.heroes[self.ID].gainAttack(4)
		self.Game.status[self.ID]["Immune"] += 1
		self.Game.status[self.ID]["ImmuneThisTurn"] += 1
		return None
		
		
class Stiltstepper(Minion):
	Class, race, name = "Demon Hunter", "", "Stiltstepper"
	mana, attack, health = 3, 4, 1
	index = "Darkmoon~Demon Hunter~Minion~3~4~1~None~Stiltstepper~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Draw a card. If you play it this turn, give your hero +4 Attack this turn"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Stiltstepper's battlecry lets player draw a card and ")
		card = self.Game.Hand_Deck.drawCard(self.ID)[0]
		if card: StiltstepperEffect(self.Game, self.ID, card).connect()
		return None
		
class StiltstepperEffect:
	def __init__(self, Game, ID, cardDrawn):
		self.Game, self.ID = Game, ID
		self.temp = False
		#Assume the trig is after the card is played
		self.signals = ["MinionBeenPlayed", "SpellBeenPlayed", "WeaponBeenPlayed", "HeroCardBeenPlayed"]
		self.cardMarked = cardDrawn
		
	def connect(self):
		for sig in self.signals:
			try: self.Game.trigsBoard[self.ID][sig].append(self)
			except: self.Game.trigsBoard[self.ID][sig] = [self]
		self.Game.turnEndTrigger.append(self)
		
	def disconnect(self):
		for sig in self.signals:
			try: self.Game.trigsBoard[self.ID][sig].remove(self)
			except: pass
		try: self.Game.turnEndTrigger.remove(self)
		except: pass
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.ID and subject == self.cardMarked
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			if self.Game.GUI: self.Game.GUI.showOffBoardTrig(Stiltstepper(self.Game, self.ID), linger=False)
			self.effect(signal, ID, subject, target, number, comment)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.Game, "The drawn card is played and Stiltstepper's effect gives player +4 Attack this turn")
		self.Game.heroes[self.ID].gainAttack(4)
		self.disconnect()
		
	def turnEndTrigger(self):
		self.disconnect()
		
	def createCopy(self, game): #不是纯的只在回合结束时触发，需要完整的createCopy
		if self not in game.copiedObjs: #这个扳机没有被复制过
			trigCopy = type(self)(game, self.ID)
			trigCopy.cardMarked = self.cardMarked.createCopy(game)
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
			
class Ilgynoth(Minion):
	Class, race, name = "Demon Hunter", "", "Il'gynoth"
	mana, attack, health = 4, 2, 6
	index = "Darkmoon~Demon Hunter~Minion~4~2~6~None~Il'gynoth~Lifesteal~Legendary"
	requireTarget, keyWord, description = False, "Lifesteal", "Lifesteal. Your Lifesteal damages the enemy hero instead of healing you"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.appearResponse = [self.activateAura]
		self.disappearResponse = [self.deactivateAura]
		self.silenceResponse = [self.deactivateAura]
		
	def activateAura(self):
		PRINT(self.Game, "Il'gynoth's aura is registered. Player %d's Lifesteal damages the enemy hero instead."%self.ID)
		self.Game.status[self.ID]["Lifesteal Damages Enemy"] += 1
		
	def deactivateAura(self):
		PRINT(self.Game, "Il'gynoth's aura is removed. Player %d's Lifesteal is back to normal"%self.ID)
		self.Game.status[self.ID]["Lifesteal Damages Enemy"] -= 1
		
		
class RenownedPerformer(Minion):
	Class, race, name = "Demon Hunter", "", "Renowned Performer"
	mana, attack, health = 4, 3, 3
	index = "Darkmoon~Demon Hunter~Minion~4~3~3~None~Renowned Performer~Rush~Deathrattle"
	requireTarget, keyWord, description = False, "Rush", "Rush. Deathrattle: Summon two 1/1 Assistants with Rush"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [Summon2Assistants(self)]
		
class Summon2Assistants(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		minion = self.entity
		pos = (minion.position, "leftandRight") if minion in minion.Game.minions[minion.ID] else (-1, "totheRightEnd")
		PRINT(minion, "Deathrattle: Summon two 1/1 Assistants with Taunt triggers.")
		minion.Game.summon([PerformersAssistant(minion.Game, minion.ID) for i in range(2)], pos, minion.ID)
		
class PerformersAssistant(Minion):
	Class, race, name = "Demon Hunter", "", "Performer's Assistant"
	mana, attack, health = 1, 1, 1
	index = "Darkmoon~Demon Hunter~Minion~1~1~1~None~Performer's Assistant~Taunt~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Taunt"
	
	
class ZaitheIncredible(Minion):
	Class, race, name = "Demon Hunter", "", "Zai, the Incredible"
	mana, attack, health = 5, 5, 3
	index = "Darkmoon~Demon Hunter~Minion~5~5~3~None~Zai, the Incredible~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Copy the left- and right-most cards in your hand"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		ownHand = self.Game.Hand_Deck.hands[self.ID]
		if ownHand:
			PRINT(self.Game, "Zai, the Incredible's battlecry copies the left- and right-most cards in player's hand")
			cards = [ownHand[0].selfCopy(self.ID), ownHand[-1].selfCopy(self.ID)]
			#Assume the copied cards BOTH occupy the right most position
			self.Game.Hand_Deck.addCardtoHand(cards, self.ID)
		return None
		
		
class BladedLady(Minion):
	Class, race, name = "Demon Hunter", "Demon", "Bladed Lady"
	mana, attack, health = 6, 6, 6
	index = "Darkmoon~Demon Hunter~Minion~6~6~6~Demon~Bladed Lady~Rush"
	requireTarget, keyWord, description = False, "Rush", "Rush. Costs (1) if your hero has 6 or more Attack"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_BladedLady(self)]
		
	def selfManaChange(self):
		if self.inHand and self.Game.heroes[self.ID].attack > 5:
			self.mana = 1
			
class Trig_BladedLady(TrigHand):
	def __init__(self, entity):
		self.blank_init(entity, ["HeroAttCalc"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand and ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Manas.calcMana_Single(self.entity)
		
		
class ExpendablePerformers(Spell):
	Class, name = "Demon Hunter", "Expendable Performers"
	requireTarget, mana = False, 7
	index = "Darkmoon~Demon Hunter~Spell~7~Expendable Performers"
	description = "Summon seven 1/1 Illidari with Rush. If they all die this turn, summon seven more"
	def available(self):
		return self.Game.space(self.ID) > 0
		#Assume you have to make all 7 die in order to summon again
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Expendable Performers summons seven 1/1 Illidari with Rush")
		minions = [IllidariInitiate(self.Game, self.ID) for i in range(7)]
		self.Game.summon(minions, (-1, "totheRightEnd"), self.ID)
		if all(minion.onBoard for minion in minions):
			Trig_ExpendablePerformers(self.Game, self.ID).connect()
		return None
		
class ExpendablePerformersEffect:
	def __init__(self, Game, ID, minions):
		self.Game, self.ID = Game, ID
		self.temp = False
		self.minions = minions
		
	def connect(self):
		try: self.Game.trigsBoard[self.ID]["TurnEnds"].append(self)
		except: self.Game.trigsBoard[self.ID]["TurnEnds"] = [self]
		try: self.Game.trigsBoard[self.ID]["MinionDies"].append(self)
		except: self.Game.trigsBoard[self.ID]["MinionDies"] = [self]
		self.Game.turnEndTrigger.append(self)
		
	def disconnect(self):
		try: self.Game.trigsBoard[self.ID]["TurnEnds"].remove(self)
		except: pass
		try: self.Game.trigsBoard[self.ID]["MinionDies"].remove(self)
		except: pass
		try: self.Game.turnEndTrigger.remove(self)
		except: pass
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return target.ID == self.ID and target in self.minions
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			if self.Game.GUI: self.Game.GUI.showOffBoardTrig(ExpendablePerformers(self.Game, self.ID), linger=False)
			self.effect(signal, ID, subject, target, number, comment)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		try: self.minions.remove(target)
		except: pass
		PRINT(self.Game, "An Illidari Initiate summoned by Expendable Performers dies. %d remaining"%len(self.minions))
		if not self.minions:
			PRINT(self.Game, "All Illidari Initiates summoned by Expendable Performers have died. Summon 7 more")
			self.disconnect()
			self.Game.summon([IllidariInitiate(self.Game, self.ID) for i in range(7)], (-1, "totheRightEnd"), self.ID)
			
	def turnEndTrigger(self):
		self.disconnect()
		
	def createCopy(self, game): #不是纯的只在回合结束时触发，需要完整的createCopy
		if self not in game.copiedObjs: #这个扳机没有被复制过
			trigCopy = type(self)(game, self.ID)
			trigCopy.minions = [minion.createCopy(game) for minion in self.minions]
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
			
"""Druid cards"""
class GuesstheWeight(Spell):
	Class, name = "Druid", "Guess the Weight"
	requireTarget, mana = False, 2
	index = "Darkmoon~Druid~Spell~2~Guess the Weight"
	description = "Draw a card. Guess if your next card costs more or less to draw it"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Guess the Weight lets player draw a card and guess if the next card costs more or less to draw it")
		card, firstCost = curGame.Hand_Deck.drawCard(self.ID)
		if card:
			if curGame.mode == 0:
				if curGame.guides:
					if curGame.guides.pop(0):
						PRINT(curGame, "Player guesses correctly and draws the next cards")
						curGame.Hand_Deck.drawCard(self.ID)
				else:
					if curGame.Hand_Deck.decks[self.ID]:
						secondCost = curGame.Hand_Deck.decks[self.ID][-1].mana
						if self.ID != curGame.turn or "byOthers" in comment:
							if npchoice([-1, 1]) * (secondCost - firstCost) > 0:
								curGame.fixedGuides.append(True)
								PRINT(curGame, "Player randomly guesses correct and draws the next cards")
								curGame.Hand_Deck.drawCard(self.ID)
							else:
								curGame.fixedGuides.append(False)
								PRINT(curGame, "Player randomly guesses incorrect")
						else:
							curGame.options = [NextCostsMore(firstCost, secondCost), NextCostsLess(firstCost, secondCost)]
							curGame.Discover.startDiscover(self)
					else: #If there isn't any card left to draw, simply don't guess
						curGame.fixedGuides.append(False)
		return None
		
	def discoverDecided(self, option, info):
		if (isinstance(option, NextCostsMore) and option.firstCost < option.secondCost) \
			or (isinstance(option, NextCostsLess) and option.firstCost > option.secondCost):
			PRINT(self.Game, "Player guessed correctly and draws the next card")
			self.Game.fixedGuides.append(True)
			self.Game.Hand_Deck.drawCard(self.ID)
		else:
			PRINT(self.Game, "Player guessed incorrectly")
			self.Game.fixedGuides.append(False)
			
class NextCostsMore:
	def __init__(self, firstCost, secondCost):
		self.name = "Costs More"
		self.description = "The next card costs more than %d"%firstCost
		self.firstCost, self.secondCost = firstCost, secondCost
		
class NextCostsLess:
	def __init__(self, firstCost, secondCost):
		self.name = "Costs Less"
		self.description = "The next card costs less than %d"%firstCost
		self.firstCost, self.secondCost = firstCost, secondCost
		
		
class LunarEclipse(Spell):
	Class, name = "Druid", "Lunar Eclipse"
	requireTarget, mana = True, 2
	index = "Darkmoon~Druid~Spell~2~Lunar Eclipse"
	description = "Deal 3 damage to a minion. Your next spell this turn costs (2) less"
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			damage = (3 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Lunar Eclipse deals %d damage to minion %s. Player's next spell this turn costs (2) less"%(damage, target.name))
			self.dealsDamage(target, damage)
			tempAura = YourNextSpellCosts2LessThisTurn(self.Game, self.ID)
			self.Game.Manas.CardAuras.append(tempAura)
			tempAura.auraAppears()
		return target
		
class SolarEclipse(Spell):
	Class, name = "Druid", "Solar Eclipse"
	requireTarget, mana = False, 2
	index = "Darkmoon~Druid~Spell~2~Solar Eclipse"
	description = "Your next spell this turn casts twice"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Solar Eclipse takes effect. Player's next spell this turn casts twice.")
		self.Game.playerStatus[self.ID]["Spells x2"] += 1
		trig = SolarEclipseEffect(self.Game, self.ID)
		trig.connect()
		return None
		
class SolarEclipseEffect:
	def __init__(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.temp = False
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.ID
		
	def connect(self):
		try: self.Game.trigsBoard[self.ID]["SpellBeenCast"].append(self)
		except: self.Game.trigsBoard[self.ID]["SpellBeenCast"] = [self]
		self.Game.turnEndTrigger.append(self)
		
	def disconnect(self):
		try: self.Game.trigsBoard[self.ID]["SpellBeenCast"].remove(self)
		except: pass
		try: self.Game.turnEndTrigger.remove(self)
		except: pass
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.Game.playerStatus[self.ID]["Spells x2"] -= 1
		self.disconnect()
		
	def turnEndTrigger(self):
		self.disconnect()
		
	def createCopy(self, game): #不是纯的只在回合结束时触发，需要完整的createCopy
		if self not in game.copiedObjs: #这个扳机没有被复制过
			trigCopy = type(self)(game, self.ID)
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
			
class FaireArborist(Minion):
	Class, race, name = "Druid", "", "Faire Arborist"
	mana, attack, health = 3, 2, 2
	index = "Darkmoon~Druid~Minion~3~2~2~None~Faire Arborist~Choose One"
	requireTarget, keyWord, description = False, "", "Choose One- Draw a card; or Summon a 2/2 Treant. Corrupt: Do both"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.chooseOne = 1
		# 0: Draw a card; 1:Summon a 2/2 Treant.
		self.options = [PrunetheFruit_Option(self), DigItUp_Option(self)]
		self.trigsHand = [Trig_Corrupt(self, FaireArborist_Corrupt)] #只有在手牌中才会升级
		
	#对于抉择随从而言，应以与战吼类似的方式处理，打出时抉择可以保持到最终结算。但是打出时，如果因为鹿盔和发掘潜力而没有选择抉择，视为到对方场上之后仍然可以而没有如果没有
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if choice != 0: #"ChooseBoth" aura gives choice of -1
			PRINT(self.Game, "Faire Arborist summons a 2/2 Treant")
			self.Game.summon(Treant_Darkmoon(self.Game, self.ID), self.position+1, self.ID)
		if choice < 1:
			PRINT(self.Game, "Faire Arborist let's player draw a card")
			self.Game.Hand_Deck.drawCard(self.ID)
		return None
		
class FaireArborist_Corrupt(Minion):
	Class, race, name = "Druid", "", "Faire Arborist"
	mana, attack, health = 3, 2, 2
	index = "Darkmoon~Druid~Minion~3~2~2~None~Faire Arborist~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "", "Corrupted. Summon a 2/2 Treant. Draw a card"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Faire Arborist summons a 2/2 Treant and lets player draw a card")
		self.Game.summon(Treant_Darkmoon(self.Game, self.ID), self.position+1, self.ID)
		self.Game.Hand_Deck.drawCard(self.ID)
		return None
		
class Treant_Darkmoon(Minion):
	Class, race, name = "Druid", "", "Treant"
	mana, attack, health = 2, 2, 2
	index = "Darkmoon~Druid~Minion~2~2~2~None~Treant~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
class PrunetheFruit_Option(ChooseOneOption):
	name, description = "Prune the Fruit", "Draw a card"
	
class DigItUp_Option(ChooseOneOption):
	name, description = "Dig It Up", "Summon a 2/2 Treant"
	def available(self):
		return self.entity.Game.space(self.entity.ID) > 0
		
		
class MoontouchedAmulet(Spell):
	Class, name = "Druid", "Moontouched Amulet"
	requireTarget, mana = False, 3
	index = "Darkmoon~Druid~Spell~3~Moontouched Amulet"
	description = "Give your hero +4 Attack this turn. Corrupt: And gain 6 Armor"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, MoontouchedAmulet_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Moontouched Amulet gives player +4 Attack this turn")
		self.Game.heroes[self.ID].gainAttack(4)
		return None
		
class MoontouchedAmulet_Corrupt(Spell):
	Class, name = "Druid", "Moontouched Amulet"
	requireTarget, mana = False, 3
	index = "Darkmoon~Druid~Spell~3~Moontouched Amulet~Corrupted~Uncollectible"
	description = "Corrupted. Give your hero +4 Attack this turn. And gain 6 Armor"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Moontouched Amulet gives player +4 Attack this turn and 6 Armor")
		self.Game.heroes[self.ID].gainAttack(4)
		self.Game.heroes[self.ID].gainsArmor(6)
		return None
		
		
class KiriChosenofElune(Minion):
	Class, race, name = "Druid", "", "Kiri, Chosen of Elune"
	mana, attack, health = 4, 2, 2
	index = "Darkmoon~Druid~Minion~4~2~2~None~Kiri, Chosen of Elune~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Add a Solar Eclipse and Lunar Eclipse to your hand"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Kiri, Chosen of Elune adds a Solar Eclipse and Lunar Eclipse to player's hand")
		self.Game.Hand_Deck.addCardtoHand([SolarEclipse, LunarEclipse], self.ID, "type")
		return None
		
		
class Greybough(Minion):
	Class, race, name = "Druid", "", "Greybough"
	mana, attack, health = 5, 4, 6
	index = "Darkmoon~Druid~Minion~5~4~6~None~Greybough~Taunt~Deathrattle~Legendary"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Deathrattle: Give a random friendly minion 'Deathrattle: Summon Greybough'"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [GiveaFriendlyDeathrattleSummonGreybough(self)]
		
class GiveaFriendlyDeathrattleSummonGreybough(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "Deathrattle: Give a random friendly minion 'Deathrattle: Summon Greybough' triggers.")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = curGame.minionsonBoard(self.entity.ID)
				i = npchoice(minions).position if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.minions[self.entity.ID][i]
				trig = SummonGreybough(minion)
				minion.deathrattles.append(trig)
				trigger.connect()
				
class SummonGreybough(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "Deathrattle: Summon a 4/6 Greybough triggers.")
		self.entity.Game.summon(Greybough(self.entity.Game, self.entity.ID), self.entity.position+1, self.entity.ID)
		
		
class UmbralOwl(Minion):
	Class, race, name = "Druid", "Beast", "Umbral Owl"
	mana, attack, health = 7, 4, 4
	index = "Darkmoon~Druid~Minion~7~4~4~Beast~Umbral Owl~Rush"
	requireTarget, keyWord, description = False, "Rush", "Rush. Costs (1) less for each spell you've cast this game"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_UmbralOwl(self)]
		
	def selfManaChange(self):
		if self.inHand:
			self.mana -= sum("~Spell~" in index for index in self.Game.Counters.cardsPlayedThisGame[self.ID])
			self.mana = max(self.mana, 0)
			
class Trig_UmbralOwl(TrigHand):
	def __init__(self, entity):
		#假设这个费用改变扳机在“当你使用一张法术之后”。不需要预检测
		self.blank_init(entity, ["SpellBeenPlayed"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand and subject.ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Manas.calcMana_Single(self.entity)
		
		
class CenarionWard(Spell):
	Class, name = "Druid", "Cenarion Ward"
	requireTarget, mana = False, 8
	index = "Darkmoon~Druid~Spell~8~Cenarion Ward"
	description = "Gain 8 Armor. Summon a random 8-Cost minion"
	poolIdentifier = "8-Cost Minions to Summon"
	@classmethod
	def generatePool(cls, Game):
		return "8-Cost Minions to Summon", list(Game.MinionsofCost[8].values())
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Cenarion Ward lets player gain 8 Armor and summons a random 8-Cost minion")
		curGame.heroes[self.ID].gainsArmor(8)
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				minion = npchoice(curGame.RNGPools["8-Cost Minions to Summon"])
				curGame.fixedGuides.append(minion)
			self.Game.summon(minion(curGame, self.ID), -1, self.ID)
		return None
		
		
class FizzyElemental(Minion):
	Class, race, name = "Druid", "Elemental", "Fizzy Elemental"
	mana, attack, health = 9, 10, 10
	index = "Darkmoon~Druid~Minion~9~10~10~Elemental~Fizzy Elemental~Rush~Taunt"
	requireTarget, keyWord, description = False, "Rush,Taunt", "Rush ,Taunt"
	
	
"""Hunter cards"""
class MysteryWinner(Minion):
	Class, race, name = "Hunter", "", "Mystery Winner"
	mana, attack, health = 1, 1, 1
	index = "Darkmoon~Hunter~Minion~1~1~1~None~Mystery Winner~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Discover a Secret"
	poolIdentifier = "Hunter Secrets"
	@classmethod
	def generatePool(cls, Game):
		classes, lists = [], []
		for Class in Game.Classes:
			secrets = [value for key, value in Game.ClassCards[Class].items() if value.description.startswith("Secret:")]
			if secrets:
				classes.append(Class+" Secrets")
				lists.append(secrets)
		return classes, lists
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if self.ID == curGame.turn:
			if curGame.mode == 0:
				if curGame.guides:
					PRINT(curGame, "Mystery Winner's battlecry adds a Secret to player's hand")
					curGame.Hand_Deck.addCardtoHand(curGame.guides.pop(0), self.ID, "type", byDiscover=True)
				else:
					key = classforDiscover(self) + " Secrets"
					if "byOthers" in comment:
						secret = npchoice(curGame.RNGPools[key])
						curGame.fixedGuides.append(secret)
						PRINT(curGame, "Mystery Winner's battlecry adds Secret to player's hand.")
						curGame.Hand_Deck.addCardtoHand(secret, self.ID, "type", byDiscover=True)
					else:
						PRINT(curGame, "Mystery Winner's battlecry lets player discover a Secret.")
						minions = npchoice(curGame.RNGPools[key], 3, replace=False)
						curGame.options = [secret(curGame, self.ID) for secret in secrets]
						curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)
		
		
class DancingCobra(Minion):
	Class, race, name = "Hunter", "Beast", "Dancing Cobra"
	mana, attack, health = 2, 1, 5
	index = "Darkmoon~Hunter~Minion~2~1~5~Beast~Dancing Cobra"
	requireTarget, keyWord, description = False, "", "Corrupt: Gain Poisonous"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, DancingCobra_Corrupt)] #只有在手牌中才会升级
		
class DancingCobra_Corrupt(Minion):
	Class, race, name = "Hunter", "Beast", "Dancing Cobra"
	mana, attack, health = 2, 1, 5
	index = "Darkmoon~Hunter~Minion~2~1~5~Beast~Dancing Cobra~Poisonous~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Poisonous", "Poisonous"
	
	
class DontFeedtheAnimals(Spell):
	Class, name = "Hunter", "Don't Feed the Animals"
	requireTarget, mana = False, 2
	index = "Darkmoon~Hunter~Spell~2~Don't Feed the Animals"
	description = "Give all Beasts in your hand +1/+1. Corrupt: Give them +2/+2 instead"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, DontFeedtheAnimals_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Don't Feed the Animals gives all Beasts in player's hand +1/+1")
		for card in self.Game.Hand_Deck.hands[self.ID]:
			if card.type == "Minion" and "Beast" in card.race:
				card.buffDebuff(1, 1)
		return None
		
class DontFeedtheAnimals_Corrupt(Spell):
	Class, name = "Hunter", "Don't Feed the Animals"
	requireTarget, mana = False, 2
	index = "Darkmoon~Hunter~Spell~2~Don't Feed the Animals~Corrupted~Uncollectible"
	description = "Corrupted. Give all Beasts in your hand +2/+2"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Don't Feed the Animals gives all Beasts in player's hand +2/+2")
		for card in self.Game.Hand_Deck.hands[self.ID]:
			if card.type == "Minion" and "Beast" in card.race:
				card.buffDebuff(2, 2)
		return None
		
		
class OpentheCages(Secret):
	Class, name = "Hunter", "Open the Cages"
	requireTarget, mana = False, 2
	index = "Darkmoon~Hunter~Spell~2~Open the Cages~~Secret"
	description = "Secret: When your turn starts, if you control two minions, summon an Animal Companion"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_OpentheCages(self)]
		
class Trig_OpentheCages(SecretTrigger):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnStarts"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0): #target here holds the actual target object
		secret = self.entity
		return secret.ID == ID and len(secret.Game.minionsonBoard(secret.ID)) > 1 and secret.Game.space(secret.ID) > 0
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "At the start of player's turn, Secret Open the Cages is triggered and summons an Animal Companion.")
		if curGame.mode == 0:
			if curGame.guides:
				companion = curGame.guides.pop(0)
			else:
				companion = npchoice([Huffer, Leokk, Misha])
				curGame.fixedGuides.append(companion)
			PRINT(curGame, "Animal Companion is cast and summons random Animal Companion %s"%companion.name)
			curGame.summon(companion(curGame, self.entity.ID), -1, self.entity.ID)
			
			
class PettingZoo(Spell):
	Class, name = "Hunter", "Petting Zoo"
	requireTarget, mana = False, 3
	index = "Darkmoon~Hunter~Spell~3~Petting Zoo"
	description = "Summon a 3/3 Strider. Repeat for each Secret you control"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Petting Zoo summons a 3/3 Strider")
		self.Game.summon(DarkmoonStrider(self.Game, self.ID), -1, self.ID)
		for i in range(len(self.Game.Secrets.secrets[self.ID])):
			PRINT(self.Game, "Petting Zoo summons a 3/3 Strider")
			self.Game.summon(DarkmoonStrider(self.Game, self.ID), -1, self.ID)
		return None
		
class DarkmoonStrider(Minion):
	Class, race, name = "Hunter", "Beast", "Darkmoon Strider"
	mana, attack, health = 3, 3, 3
	index = "Darkmoon~Hunter~Minion~3~3~3~Beast~Darkmoon Strider~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
	
class RinlingsRifle(Weapon):
	Class, name, description = "Hunter", "Rinling's Rifle", "After your hero attacks, Discover a Secret and cast it"
	mana, attack, durability = 4, 2, 2
	index = "Darkmoon~Hunter~Weapon~4~2~2~Rinling's Rifle~Legendary"
	poolIdentifier = "Hunter Secrets"
	@classmethod
	def generatePool(cls, Game):
		classes, lists = [], []
		for Class in Game.Classes:
			secrets = [value for key, value in Game.ClassCards[Class].items() if value.description.startswith("Secret:")]
			if secrets:
				classes.append(Class+" Secrets")
				lists.append(secrets)
		return classes, lists
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_RinlingsRifle(self)]
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		option.cast()
		
class Trig_RinlingsRifle(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["HeroAttackedMinion", "HeroAttackedHero"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject == self.entity.Game.heroes[self.entity.ID] and self.entity.onBoard
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		weapon, curGame = self.entity, self.entity.Game
		if curGame.mode == 0:
			PRINT(curGame, "After player attacks, Rinling's Rifle lets player Discover a Secret and cast it")
			if curGame.guides:
				curGame.guides.pop(0)(curGame, weapon.ID).cast()
			else:
				PRINT(curGame, "After player plays a Secret, Rinling's Rifle lets player Discover a spell")
				key = classforDiscover(weapon)+" Secrets"
				secrets = npchoice(curGame.RNGPools[key], 3, replace=False)
				curGame.options = [secrets(curGame, weapon.ID) for secrets in spells]
				curGame.Discover.startDiscover(weapon)
				
				
class TramplingRhino(Minion):
	Class, race, name = "Hunter", "Beast", "Trampling Rhino"
	mana, attack, health = 5, 5, 5
	index = "Darkmoon~Hunter~Minion~5~5~5~Beast~Trampling Rhino~Rush"
	requireTarget, keyWord, description = False, "Rush", "Rush. Afte this attacks and kills a minion, excess damage hits the enemy hero"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_TramplingRhino(self)]
		
class Trig_TramplingRhino(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAttackedMinion"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject == self.entity and self.entity.health > 0 and self.entity.dead == False and target.health < 0
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		excessDmg = -target.health
		PRINT(self.entity.Game, "After Trampling Rhino attacks and kills a minion %s, it deals the excess damage to the enemy hero."%target.name)
		self.entity.dealsDamage(self.entity.Game.heroes[3-self.entity.ID], excessDmg)
		
		
class MaximaBlastenheimer(Minion):
	Class, race, name = "Hunter", "", "Maxima Blastenheimer"
	mana, attack, health = 6, 4, 4
	index = "Darkmoon~Hunter~Minion~6~4~4~None~Maxima Blastenheimer~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Summon a random minion from your deck. It attacks the enemy hero, then dies"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Maxima Blastenheimer's battlecry summons a random minion from player's deck. It attacks the enemy hero and dies")
		if curGame.mode == 0:
			if curGame.guides: #Summon a demon from deck
				i = curGame.guides.pop(0)
			else: #Find demons in hand
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions and curGame.space(self.ID) > 0 else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.summonfromDeck(i, self.ID, self.position+1, self.ID)
				if minion:
					#verifySelectable is exclusively for player ordering chars to attack
					curGame.battle(minion, curGame.heroes[3-self.ID], verifySelectable=False, useAttChance=True, resolveDeath=False, resetRedirectionTriggers=True)
					if minion.onBoard: curGame.killMinion(self, minion)
					curGame.gathertheDead()
		return None
		
		
class DarkmoonTonk(Minion):
	Class, race, name = "Hunter", "Mech", "Darkmoon Tonk"
	mana, attack, health = 7, 8, 5
	index = "Darkmoon~Hunter~Minion~7~8~5~Mech~Darkmoon Tonk~Deathrattle"
	requireTarget, keyWord, description = False, "", "Deathrattle: Fire four missiles at random enemies that deal 2 damage each"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [Fire4Missiles(self)]
		
class Fire4Missiles(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		minion = self.entity
		curGame = minion.Game
		if curGame.mode == 0:
			PRINT(curGame, "Deathrattle: Fire 4 missiles at random enemies that deal 2 damage each")
			for num in range(4):
				enemy = None
				if curGame.guides:
					i, where = curGame.guides.pop(0)
					if where: enemy = curGame.find(i, where)
				else:
					enemies = curGame.charsAlive(3-minion.ID)
					if enemies:
						enemy = npchoice(enemies)
						curGame.fixedGuides.append((enemy.position, enemy.type+str(enemy.ID)))
					else:
						curGame.fixedGuides.append((0, ''))
				if enemy:
					PRINT(curGame, "Deathrattle deals 2 damage to random enemy %s"%enemy.name)
					minion.dealsDamage(enemy, 2)
				else: break
				
				
class JewelofNZoth(Spell):
	Class, name = "Hunter", "Jewel of N'Zoth"
	requireTarget, mana = False, 8
	index = "Darkmoon~Hunter~Spell~8~Jewel of N'Zoth"
	description = "Summon three friendly Deathrattle minions that died this game"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Jewel of N'Zoth summons 3 friendly Deathrattle minions that died this game")
			if curGame.guides:
				minions = curGame.guides.pop(0)
			else:
				minionsDied = [index for index in curGame.Counters.minionsDiedThisGame[self.ID] if "~Deathrattle" in index]
				indices = npchoice(minionsDied, min(3, len(minionsDied)), replace=False) if minionsDied else []
				minions = tuple([curGame.cardPool[index] for index in indices])
				curGame.fixedGuides.append(minions)
			if minions: curGame.summon([minion(curGame, self.ID) for minion in minions], (-1, "totheRightEnd"), self.ID)
		return None
		
"""Mage cards"""
class ConfectionCyclone(Minion):
	Class, race, name = "Mage", "Elemental", "Confection Cyclone"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Mage~Minion~2~3~2~Elemental~Confection Cyclone~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Add two 1/1 Sugar Elementals to your hand"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Confection Cyclone's battlecry adds two 1/1 Sugar Elementals to player's hand")
		self.Game.Hand_Deck.addCardtoHand([SugarElemental, SugarElemental], self.ID, "type")
		return None
		
class SugarElemental(Minion):
	Class, race, name = "Mage", "Elemental", "Sugar Elemental"
	mana, attack, health = 1, 1, 1
	index = "Darkmoon~Mage~Minion~1~1~1~Elemental~Sugar Elemental~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
	
class DeckofLunacy(Spell):
	Class, name = "Mage", "Deck of Lunacy"
	requireTarget, mana = False, 2
	index = "Darkmoon~Mage~Spell~2~Deck of Lunacy~Legendary"
	description = "Transform spells in your deck into ones that cost (3) more. (They keep their original Cost.)"
	poolIdentifier = "3-Cost Spells"
	@classmethod
	def generatePool(cls, Game):
		spells = {mana: [] for mana in range(3, 11)}
		for Class in Game.Classes:
			for key, value in Game.ClassCards[Class].items():
				if "~Spell~" in key:
					spells[value.mana].append(value)
		return ["%d-Cost Spells"%cost for cost in spells.keys()], list(spells.values())
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame, ID = self.Game, self.ID
		PRINT(curGame, "Deck of Lunacy transforms spells in player's deck into ones that cost (3) more")
		if curGame.mode == 0:
			if curGame.guides:
				indices, newCardsm, costs = curGame.guides.pop(0)
			else:
				indices, newCards, costs = [], [], []
				for i, card in enumerate(curGame.Hand_Deck.decks[ID]):
					if card.type == "Spell":
						indices.append(i)
						newCards.append(npchoice(curGame.RNGPools["%d-Cost Spells"%min(10, card.mana+3)]))
						costs.append(card.mana)
			if indices:
				newCards = [card(curGame, ID) for card in newCards]
				for card, cost in zip(newCards, costs):
					ManaMod(card, changeby=-1, changeto=cost).applies()
				curGame.Hand_Deck.replacePartofDeck(ID, indices, newCards)
		return None
		
		
class GameMaster(Minion):
	Class, race, name = "Mage", "", "Game Master"
	mana, attack, health = 2, 2, 2
	index = "Darkmoon~Mage~Minion~2~2~2~None~Game Master"
	requireTarget, keyWord, description = False, "", "The first Secret you play each turn costs (1)"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.auras["Mana Aura"] = ManaAura_Dealer(self, changeby=0, changeto=-1)
		self.trigsBoard = [Trig_GameMaster(self)]
		#随从的光环启动在顺序上早于appearResponse,关闭同样早于disappearResponse
		self.appearResponse = [self.checkAuraCorrectness]
		self.disappearResponse = [self.deactivateAura]
		self.silenceResponse = [self.deactivateAura]
		
	def manaAuraApplicable(self, target):
		return target.ID == self.ID and target.description.startswith("Secret:")
		
	def checkAuraCorrectness(self): #负责光环在随从登场时无条件启动之后的检测。如果光环的启动条件并没有达成，则关掉光环
		if self.Game.turn != self.ID or any(index.endswith("~~Secret") for index in self.Game.Counters.cardsPlayedThisTurn[self.ID]["Indices"]):
			self.auras["Mana Aura"].auraDisappears()
			
	def deactivateAura(self): #随从被沉默时优先触发disappearResponse,提前关闭光环，之后auraDisappears可以再调用一次，但是没有作用而已
		self.auras["Mana Aura"].auraDisappears()
		
class Trig_GameMaster(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnStarts", "TurnEnds", "ManaPaid"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and ("Turn" in signal and ID == self.entity.ID) \
			or (signal == "ManaPaid" and subject.type == "Minion" and subject.ID == self.entity.ID)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		if "Turn" in signal: #回合开始结束时总会强制关闭然后启动一次光环。这样，即使回合开始或者结束发生了随从的控制变更等情况，依然可以保证光环的正确
			PRINT(self.entity.Game, "At the start of turn, Game Master restarts the mana aura and reduces the cost of the first Secret to (1).")
			self.entity.auras["Mana Aura"].auraDisappears()
			self.entity.auras["Mana Aura"].auraAppears()
			self.entity.checkAuraCorrectness()
		else: #signal == "ManaPaid"
			self.entity.auras["Mana Aura"].auraDisappears()
			
			
class RiggedFaireGame(Secret):
	Class, name = "Mage", "Rigged Faire Game"
	requireTarget, mana = False, 3
	index = "Darkmoon~Mage~Spell~3~Rigged Faire Game~~Secret"
	description = "Secret: If you didn't take any damage during your opponent's turn, draw 3 cards"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_RiggedFaireGame(self)]
		
class Trig_RiggedFaireGame(SecretTrigger):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnEnds"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0): #target here holds the actual target object
		return self.entity.ID != ID and self.entity.Game.Counters.dmgonHero_inOppoTurn[self.entity.ID] == 0
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "Player took no damage in opponent's turn, Secret Rigged Faire Game is triggered and player draws 3 cards.")
		self.entity.Game.Hand_Deck.drawCard(self.entity.ID)
		
		
class OccultConjurer(Minion):
	Class, race, name = "Mage", "", "Occult Conjurer"
	mana, attack, health = 4, 4, 4
	index = "Darkmoon~Mage~Minion~4~4~4~None~Occult Conjurer~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: If you control a Secret, summon a copy of this"
	
	def effectCanTrigger(self):
		self.effectViable = self.Game.Secrets.secrets[self.ID] != []
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.Game.Secrets.secrets[self.ID]:
			PRINT(self.Game, "Occult Conjurer's battlecry summons a copy of the minion")
			Copy = self.selfCopy(self.ID) if self.onBoard else type(self)(self.Game, self.ID)
			self.Game.summon(Copy, self.position+1, self.ID)
		return None
		
		
class RingToss(Spell):
	Class, name = "Mage", "Ring Toss"
	requireTarget, mana = False, 4
	index = "Darkmoon~Mage~Spell~4~Ring Toss"
	description = "Discover a Secret and cast it. Corrupt: Discover 2 instead"
	poolIdentifier = "Mage Secrets"
	@classmethod
	def generatePool(cls, Game):
		classes, lists = [], []
		for Class in Game.Classes:
			secrets = [value for key, value in Game.ClassCards[Class].items() if value.description.startswith("Secret:")]
			if secrets:
				classes.append(Class+" Secrets")
				lists.append(secrets)
		return classes, lists
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, RingToss_Corrupted)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if self.ID == curGame.turn:
			if curGame.mode == 0:
				if curGame.guides:
					PRINT(curGame, "Ring Toss casts a Secret")
					curGame.guides.pop(0)(self.Game, self.ID).cast()
				else:
					key = classforDiscover(self) + " Secrets"
					if self.ID != curGame.turn or "byOthers" in comment:
						secret = npchoice(curGame.RNGPools[key])
						curGame.fixedGuides.append(secret)
						PRINT(curGame, "Ring Toss casts a random Secret")
						secret(self.Game, self.ID).cast()
					else:
						PRINT(curGame, "Ring Toss lets player discover a Secret to cast")
						secrets = npchoice(curGame.RNGPools[key], 3, replace=False)
						curGame.options = [secret(curGame, self.ID) for secret in secrets]
						curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		option.cast()
		
class RingToss_Corrupted(Spell):
	Class, name = "Mage", "Ring Toss"
	requireTarget, mana = False, 4
	index = "Darkmoon~Mage~Spell~4~Ring Toss~Corrupted~Uncollectible"
	description = "Corrupted. Discover 2 Secrets and cast them"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if self.ID == curGame.turn:
			if curGame.mode == 0:
				for num in range(2):
					if curGame.guides:
						PRINT(curGame, "Ring Toss casts a Secret")
						curGame.guides.pop(0)(self.Game, self.ID).cast()
					else:
						key = classforDiscover(self) + " Secrets"
						if self.ID != curGame.turn or "byOthers" in comment:
							secret = npchoice(curGame.RNGPools[key])
							curGame.fixedGuides.append(secret)
							PRINT(curGame, "Ring Toss casts a random Secret")
							secret(self.Game, self.ID).cast()
						else:
							PRINT(curGame, "Ring Toss lets player discover a Secret to cast")
							secrets = npchoice(curGame.RNGPools[key], 3, replace=False)
							curGame.options = [secret(curGame, self.ID) for secret in secrets]
							curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		option.cast()
		
		
class FireworkElemental(Minion):
	Class, race, name = "Mage", "Elemental", "Firework Elemental"
	mana, attack, health = 5, 3, 5
	index = "Darkmoon~Mage~Minion~5~3~5~Elemental~Firework Elemental~Battlecry"
	requireTarget, keyWord, description = True, "", "Battlecry: Deal 3 damage to a minion. Corrupt: Deal 12 damage instead"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, FireworkElemental_Corrupted)] #只有在手牌中才会升级
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Firework Elemental's battlecry deals 3 damage to minion %s"%target.name)
			self.dealsDamage(target, 3)
		return target
		
class FireworkElemental(Minion):
	Class, race, name = "Mage", "Elemental", "Firework Elemental"
	mana, attack, health = 5, 3, 5
	index = "Darkmoon~Mage~Minion~5~3~5~Elemental~Firework Elemental~Battlecry~Corrupted~Uncollectible"
	requireTarget, keyWord, description = True, "", "Corrupted. Battlecry: Deal 12 damage to a minion"
	
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Firework Elemental's battlecry deals 12 damage to minion %s"%target.name)
			self.dealsDamage(target, 12)
		return target
		
		
class SaygeSeerofDarkmoon(Minion):
	Class, race, name = "Mage", "", "Sayge, Seer of Darkmoon"
	mana, attack, health = 6, 5, 5
	index = "Darkmoon~Mage~Minion~6~5~5~None~Sayge, Seer of Darkmoon~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Draw 1 card(Upgraded for each friendly Secret that has triggered this game!)"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		num = curGame.Counters.numSecretsTriggeredThisGame[self.ID] + 1
		PRINT(curGame, "Sayge, Seer of Darkmoon's battlecry lets player draw %d cards"%num)
		for i in range(num):
			curGame.Hand_Deck.drawCard(self.ID)
		return None
		
		
class MaskofCThun(Spell):
	Class, name = "Mage", "Mask of C'Thun"
	requireTarget, mana = False, 7
	index = "Darkmoon~Mage~Spell~7~Mask of C'Thun"
	description = "Deal 10 damage randomly split among all enemies"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		damage = (10 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
		side, curGame = 3-self.ID, self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Mask of C'Thun launches %d missiles."%damage)
			for num in range(damage):
				char = None
				if curGame.guides:
					i, where = curGame.guides.pop(0)
					if where: char = curGame.find(i, where)
				else:
					objs = curGame.charsAlive(side)
					if objs:
						char = npchoice(objs)
						curGame.fixedGuides.append((char.position, char.type+str(side)))
					else:
						curGame.fixedGuides.append((0, ''))
				if char:
					self.dealsDamage(char, 1)
				else: break
		return None
		
		
class GrandFinale(Spell):
	Class, name = "Mage", "Grand Finale"
	requireTarget, mana = False, 8
	index = "Darkmoon~Mage~Spell~8~Grand Finale"
	description = "Summon an 8/8 Elemental. Repeat for each Elemental you played last turn"
	def effectCanTrigger(self):
		self.effectViable = self.Game.Counters.numElementalsPlayedLastTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Grand Finale summons an 8/8 Elemental and repeats for each Elemental the player played last turn")
		curGame.summon(ExplodingSparkler(curGame, self.ID), -1, self.ID)
		for i in range(curGame.Counters.numElementalsPlayedLastTurn[self.ID]):
			curGame.summon(ExplodingSparkler(curGame, self.ID), -1, self.ID)
		return target
		
class ExplodingSparkler(Minion):
	Class, race, name = "Mage", "Elemental", "Exploding Sparkler"
	mana, attack, health = 8, 8, 8
	index = "Darkmoon~Mage~Minion~8~8~8~Elemental~Exploding Sparkler~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
"""Paladin cards"""
class OhMyYogg(Secret):
	Class, name = "Paladin", "Oh My Yogg!"
	requireTarget, mana = False, 1
	index = "Darkmoon~Paladin~Spell~1~Oh My Yogg!~~Secret"
	description = "Secret: When your opponent casts a spell, they instead cast a random one of the same Cost"
	poolIdentifier = "0-Cost Spells"
	@classmethod
	def generatePool(cls, Game):
		spells = {mana: [] for mana in range(0, 11)}
		for Class in Game.Classes:
			for key, value in Game.ClassCards[Class].items():
				if "~Spell~" in key:
					spells[value.mana].append(value)
		return ["%d-Cost Spells"%cost for cost in spells.keys()], list(spells.values())
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_OhMyYogg(self)]
		
class Trig_OhMyYogg(SecretTrigger):
	def __init__(self, entity):
		self.blank_init(entity, ["SpellOKtoCast?"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID != self.entity.ID and subject
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "Secret Oh My Yogg! turns the spell %s the opponent plays into a randomly cast one of the same cost%s"%subject[0].name)
		if curGame.mode == 0:
			if curGame.guides:
				newSpell = curGame.guides.pop(0)
			else:
				newSpell = npchoice(curGame.RNGPools["%d-Cost Spells"%number])
				curGame.fixedGuides.append(newSpell)
			subject[0] = newSpell(curGame, self.entity.ID)
			
			
class RedscaleDragontamer(Minion):
	Class, race, name = "Paladin", "Murloc", "Redscale Dragontamer"
	mana, attack, health = 2, 2, 3
	index = "Darkmoon~Paladin~Minion~2~2~3~Murloc~Redscale Dragontamer~Battlecry"
	requireTarget, keyWord, description = False, "", "Deathrattle: Draw a Dragon"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [DrawaDragon(self)]
		
class DrawaDragon(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "Deathrattle: Draw a Dragon triggers")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.entity.ID]) if card.type == "Minion" and "Dragon" in card.race]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.Hand_Deck.drawCard(self.entity.ID, i)[0]
			
			
class SnackRun(Spell):
	Class, name = "Paladin", "Snack Run"
	requireTarget, mana = False, 2
	index = "Darkmoon~Paladin~Spell~2~Snack Run"
	description = "Discover a spell. Restore Health to your hero equal to its Cost"
	poolIdentifier = "Paladin Spells"
	@classmethod
	def generatePool(cls, Game):
		return [Class+" Spells" for Class in Game.Classes], \
				[[value for key, value in Game.ClassCards[Class].items() if "~Spell~" in key] for Class in Game.Classes]
				
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				card = curGame.guides.pop(0)
				PRINT(curGame, "Snack Run adds a spell to player's hand. And restores %d Health to player"%card.mana)
				curGame.Hand_Deck.addCardtoHand(card, self.ID, "type", byDiscover=True)
				heal = card.mana * (2 ** self.countHealDouble())
				self.restoresHealth(curGame.heroes[self.ID], heal)
			else:
				key = classforDiscover(self)+" Spells"
				if self.ID != curGame.turn or "byOthers" in comment:
					spell = npchoice(curGame.RNGPools[key])
					curGame.fixedGuides.append(spell)
					PRINT(curGame, "Palm Reading is cast and adds a random spell to player's hand. And restores %d Health to player"%spell.mana)
					curGame.Hand_Deck.addCardtoHand(spell, self.ID, "type", byDiscover=True)
					heal = spell.mana * (2 ** self.countHealDouble())
					self.restoresHealth(curGame.heroes[self.ID], heal)
				else:
					PRINT(curGame, "Palm Reading lets player discover a spell")
					spells = npchoice(curGame.RNGPools[key], 3, replace=False)
					curGame.options = [spell(curGame, self.ID) for spell in spells]
					curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		cost = option.mana
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)
		PRINT(self.Game, "Snack Run restores %d Health to player"%cost)
		heal = cost * (2 ** self.countHealDouble())
		self.restoresHealth(curGame.heroes[self.ID], heal)
		
		
class CarnivalBarker(Minion):
	Class, race, name = "Paladin", "", "Carnival Barker"
	mana, attack, health = 3, 3, 2
	index = "Darkmoon~Paladin~Minion~3~3~2~None~Carnival Barker"
	requireTarget, keyWord, description = False, "", "Whenever you summon a 1-Health minion, give +1/+2"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_CarnivalBarker(self)]
		
class Trig_CarnivalBarker(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionSummoned"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject.ID == self.entity.ID and subject.health == 1 and subject != self.entity
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "A friendly 1-Health minion %s is summoned and Carnival Barker gains +1/+2"%subject.name)
		subject.buffDebuff(1, 2)
		
		
class DayattheFaire(Spell):
	Class, name = "Paladin", "Day at the Faire"
	requireTarget, mana = False, 3
	index = "Darkmoon~Paladin~Spell~3~Day at the Faire"
	description = "Summon 3 Silver Hand Recruits. Corrupt: Summon 5"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, DayattheFaire_Corrupt)] #只有在手牌中才会升级
		
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		curGame = self.Game
		PRINT(curGame, "Day at the Faire summons 3 Silver Hand Recruits")
		curGame.summon([SilverHandRecruit(curGame, self.ID) for i in range(3)], (-1, "totheRightEnd"), self.ID)
		return None
		
class DayattheFaire_Corrupt(Spell):
	Class, name = "Paladin", "Day at the Faire"
	requireTarget, mana = False, 3
	index = "Darkmoon~Paladin~Spell~3~Day at the Faire~Corrupted~Uncollectible"
	description = "Corrupted: Summon 5 Silver Hand Recruits"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		curGame = self.Game
		PRINT(curGame, "Day at the Faire summons 5 Silver Hand Recruits")
		curGame.summon([SilverHandRecruit(curGame, self.ID) for i in range(5)], (-1, "totheRightEnd"), self.ID)
		return None
		
		
class BalloonMerchant(Minion):
	Class, race, name = "Paladin", "", "Balloon Merchant"
	mana, attack, health = 4, 3, 5
	index = "Darkmoon~Paladin~Minion~4~3~5~None~Balloon Merchant~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Give your Silver Hand Recruits +1 Attack and Divine Shield"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(curGame, "Balloon Merchant's battlecry gvies player's Silver Hand Recruits +1 Attack and Divine Shield")
		for minion in self.Game.minionsonBoard(self.ID):
			if minion.name == "Silver Hand Recruit":
				minion.buffDebuff(1, 0)
				minion.getsKeyword("Divine Shield")
		return None
		
		
class CarouselGryphon(Minion):
	Class, race, name = "Paladin", "Mech", "Carousel Gryphon"
	mana, attack, health = 5, 5, 5
	index = "Darkmoon~Paladin~Minion~5~5~5~Mech~Carousel Gryphon~Divine Shield"
	requireTarget, keyWord, description = False, "Divine Shield", "Divine Shield. Corrupt: Gain +3/+3 and Taunt"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, CarouselGryphon_Corrupted)] #只有在手牌中才会升级
		
class CarouselGryphon_Corrupted(Minion):
	Class, race, name = "Paladin", "Mech", "Carousel Gryphon"
	mana, attack, health = 5, 8, 8
	index = "Darkmoon~Paladin~Minion~5~8~8~Mech~Carousel Gryphon~Divine Shield~Taunt~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Divine Shield,Taunt", "Divine Shield, Taunt"
	
	
class LothraxiontheRedeemed(Minion):
	Class, race, name = "Paladin", "Demon", "Lothraxion the Redeemed"
	mana, attack, health = 5, 5, 5
	index = "Darkmoon~Paladin~Minion~5~5~5~Demon~Lothraxion the Redeemed~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: For the rest of the game, after you summon a Silver Hand Recruit, give it Divine Shield"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(curGame, "Lothraxion the Redeemed's battlecry gives every Silver Hand Recruit summoned by player for the rest of the turn")
		LothraxiontheRedeemedEffect(self.Game, self.ID).connect()
		return None
		
class LothraxiontheRedeemedEffect:
	def __init__(self, Game, ID, cardDrawn):
		self.Game, self.ID = Game, ID
		self.temp = False
		#Assume the trig is when the card is played
		self.signals = ["MinionBeenSummoned"]
		
	def connect(self):
		try: self.Game.trigsBoard[self.ID]["MinionBeenSummoned"].append(self)
		except: self.Game.trigsBoard[self.ID]["MinionBeenSummoned"] = [self]
		
	def disconnect(self):
		try: self.Game.trigsBoard[self.ID]["MinionBeenSummoned"].remove(self)
		except: pass
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.ID and subject.name == "Silver Hand Recruit"
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			if self.Game.GUI: self.Game.GUI.showOffBoardTrig(LothraxiontheRedeemed(self.Game, self.ID), linger=False)
			self.effect(signal, ID, subject, target, number, comment)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		subject.getsKeyword("Divine Shield")
		self.disconnect()
		
	def createCopy(self, game): #不是纯的只在回合结束时触发，需要完整的createCopy
		if self not in game.copiedObjs: #这个扳机没有被复制过
			trigCopy = type(self)(game, self.ID)
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
			
class HammeroftheNaaru(Weapon):
	Class, name, description = "Paladin", "Hammer of the Naaru", "Battlecry: Summon a 6/6 Holy Elemental with Taunt"
	mana, attack, durability = 6, 3, 3
	index = "Darkmoon~Paladin~Weapon~6~3~3~Hammer of the Naaru~Battlecry"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Hammer of the Naaru's batlecry summons a 6/6 Holy Elemental with Taunt")
		self.Game.summon(HolyElemental(self.Game, self.ID), -1, self.ID)
		return None
		
class HolyElemental(Minion):
	Class, race, name = "Paladin", "Elemental", "Holy Elemental"
	mana, attack, health = 6, 6, 6
	index = "Darkmoon~Paladin~Minion~6~6~6~None~Holy Elemental~Taunt~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Taunt"
	
	
class HighExarchYrel(Minion):
	Class, race, name = "Paladin", "", "High Exarch Yrel"
	mana, attack, health = 8, 7, 5
	index = "Darkmoon~Paladin~Minion~8~7~5~None~High Exarch Yrel~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: If your deck has no Neutral cards, gain Rush, Lifesteal, Taunt, and Divine Shield"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if all(card.Class != "Neutral" for card in self.Game.Hand_Deck.decks[self.ID]):
			PRINT(curGame, "High Exarch Yrel's battlecry gvies the minion Rush, Lifesteal, Taunt, and Divine Shield")
			self.getsKeyword("Rush")
			self.getsKeyword("Lifesteal")
			self.getsKeyword("Taunt")
			self.getsKeyword("Divine Shield")
		return None
		
"""Priest cards"""
class Insight(Spell):
	Class, name = "Priest", "Insight"
	requireTarget, mana = False, 2
	index = "Darkmoon~Priest~Spell~2~Insight"
	description = "Draw a minion. Corrupt: Reduce its Cost by (2)"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, Insight_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Insight lets player draw a minion from deck")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.Hand_Deck.drawCard(self.ID, i)
		return None
		
class Insight_Corrupt(Spell):
	Class, name = "Priest", "Insight"
	requireTarget, mana = False, 2
	index = "Darkmoon~Priest~Spell~2~Insight~Corrupted~Uncollectible"
	description = "Corrupted. Draw a minion. Reduce its Cost by (2)"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Insight lets player draw a minion from deck")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.Hand_Deck.drawCard(self.ID, i)[0]
				if minion:
					PRINT(curGame, "Insight reduces the Cost of the draw minion by (2)")
					ManaMod(minion, changeby=-2, changeto=-1).applies()
		return None
		
		
class FairgroundFool(Minion):
	Class, race, name = "Priest", "", "Fairground Fool"
	mana, attack, health = 3, 4, 3
	index = "Darkmoon~Priest~Minion~3~4~3~None~Fairground Fool~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Corrupt: Gain +4 Health"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, FairgroundFool_Corrupt)] #只有在手牌中才会升级
		
class FairgroundFool_Corrupt(Minion):
	Class, race, name = "Priest", "", "Fairground Fool"
	mana, attack, health = 3, 4, 7
	index = "Darkmoon~Priest~Minion~3~4~7~None~Fairground Fool~Taunt~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Corrupted. Taunt"
	
	
class NazmaniBloodweaver(Minion):
	Class, race, name = "Priest", "", "Nazmani Bloodweaver"
	mana, attack, health = 3, 2, 5
	index = "Darkmoon~Priest~Minion~3~2~5~None~Nazmani Bloodweaver"
	requireTarget, keyWord, description = False, "", "After you cast a spell, reduce the Cost of a random card in your hand by (1)"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_NazmaniBloodweaver(self)]
		
class Trig_NazmaniBloodweaver(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["SpellBeenPlayed"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject.ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			PRINT(curGame, "After player casts spell, Nazmani Bloodweaver reduces the Cost of a random card in player's hand by (1)")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				num = len(curGame.Hand_Deck.hands[self.entity.ID])
				i = nprandint(num) if num else -1
			if i > -1:
				ManaMod(curGame.Hand_Deck.hands[self.entity.ID][i], changeby=-1, changeto=-1).applies()
				
				
class PalmReading(Spell):
	Class, name = "Priest", "Palm Reading"
	requireTarget, mana = False, 3
	index = "Darkmoon~Priest~Spell~3~Palm Reading"
	description = "Discover a spell. Reduce the Cost of spells in your hand by (1)"
	poolIdentifier = "Priest Spells"
	@classmethod
	def generatePool(cls, Game):
		return [Class+" Spells" for Class in Game.Classes], \
				[[value for key, value in Game.ClassCards[Class].items() if "~Spell~" in key] for Class in Game.Classes]
				
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				PRINT(curGame, "Palm Reading adds a spell to player's hand")
				curGame.Hand_Deck.addCardtoHand(curGame.guides.pop(0), self.ID, "type", byDiscover=True)
			else:
				key = classforDiscover(self)+" Spells"
				if self.ID != curGame.turn or "byOthers" in comment:
					spell = npchoice(curGame.RNGPools[key])
					curGame.fixedGuides.append(spell)
					PRINT(curGame, "Palm Reading is cast and adds a random spell to player's hand")
					curGame.Hand_Deck.addCardtoHand(spell, self.ID, "type", byDiscover=True)
				else:
					PRINT(curGame, "Palm Reading lets player discover a spell")
					spells = npchoice(curGame.RNGPools[key], 3, replace=False)
					curGame.options = [spell(curGame, self.ID) for spell in spells]
					curGame.Discover.startDiscover(self)
		PRINT(curGame, "Palm Reading reduces the Cost of spells in player's hand by (1)")
		for card in self.Game.Hand_Deck.hands[self.ID]:
			if card.type == "Spell":
				ManaMod(card, changeby=-1, changeto=-1).applies()
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)
		
		
class AuspiciousSpirits(Spell):
	Class, name = "Priest", "Auspicious Spirits"
	requireTarget, mana = False, 4
	index = "Darkmoon~Priest~Spell~4~Auspicious Spirits"
	description = "Summon a random 4-Cost minion. Corrupt: Summon a 7-Cost minion instead"
	poolIdentifier = "4-Cost Minions to Summon"
	@classmethod
	def generatePool(cls, Game):
		return "4-Cost Minions to Summon", list(Game.MinionsofCost[4].values())
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, AuspiciousSpirits_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Auspicious Spirits summons a random 4-Cost minion")
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				minion = npchoice(curGame.RNGPools["4-Cost Minions to Summon"])
				curGame.fixedGuides.append(minion)
			self.Game.summon(minion(curGame, self.ID), -1, self.ID)
		return None
		
class AuspiciousSpirits_Corrupt(Spell):
	Class, name = "Priest", "Auspicious Spirits"
	requireTarget, mana = False, 4
	index = "Darkmoon~Priest~Spell~4~Auspicious Spirits~Corrupted~Uncollectible"
	description = "Corrupted. Summon a 7-Cost minion"
	poolIdentifier = "7-Cost Minions to Summon"
	@classmethod
	def generatePool(cls, Game):
		return "7-Cost Minions to Summon", list(Game.MinionsofCost[7].values())
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Auspicious Spirits summons a random 7-Cost minion")
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				minion = npchoice(curGame.RNGPools["7-Cost Minions to Summon"])
				curGame.fixedGuides.append(minion)
			self.Game.summon(minion(curGame, self.ID), -1, self.ID)
		return None
		
		
class TheNamelessOne(Minion):
	Class, race, name = "Priest", "", "The Nameless One"
	mana, attack, health = 4, 4, 4
	index = "Darkmoon~Priest~Minion~4~4~4~None~The Nameless One~Battlecry~Legendary"
	requireTarget, keyWord, description = True, "", "Battlecry: Choose a minion. Become a copy of it, then Silence it"
	
	def targetExists(self, choice=0):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target != self and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "The Nameless One's battlecry transforms minion into a copy of %s"%target.name)
			if not self.dead and self.Game.minionPlayed == self and (self.onBoard or self.inHand): #战吼触发时自己不能死亡。
				Copy = target.selfCopy(self.ID) if target.onBoard or target.inHand else type(target)(self.Game, self.ID)
				self.Game.transform(self, Copy)
			target.getsSilenced()
		return target
		
		
class FortuneTeller(Minion):
	Class, race, name = "Priest", "", "Fortune Teller"
	mana, attack, health = 5, 3, 3
	index = "Darkmoon~Priest~Minion~5~3~3~None~Fortune Teller~Taunt~Battlecry"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Battlecry: Gain +1/+1 for each spell in your hand"
	#For self buffing effects, being dead and removed before battlecry will prevent the battlecry resolution.
	#If this minion is returned hand before battlecry, it can still buff it self according to living friendly minions.
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.onBoard or self.inHand: #For now, no battlecry resolution shuffles this into deck.
			num = sum(card.type == "Spell" for card in self.Game.Hand_Deck.hands[self.ID])
			PRINT(self.Game, "Fortune Teller's battlecry gives minion +1/+1 for each spell in player's hand.")
			self.buffDebuff(num, num)
		return None
		
		
class IdolofYShaarj(Spell):
	Class, name = "Priest", "Idol of Y'Shaarj"
	requireTarget, mana = False, 8
	index = "Darkmoon~Priest~Spell~8~Idol of Y'Shaarj"
	description = "Summon a 10/10 copy of a minion in your deck"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Idol of Y'Shaarj summons a 10/10 of a minion in player's deck")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				curGame.summon(curGame.Hand_Deck.decks[self.ID][i].selfCopy(self.ID), -1, self.ID)
		return None
		
		
class GhuuntheBloodGod(Minion):
	Class, race, name = "Priest", "", "G'huun the Blood God"
	mana, attack, health = 8, 8, 8
	index = "Darkmoon~Priest~Minion~8~8~8~None~G'huun the Blood God~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Draw 2 cards. They cost Health instead of Mana"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "G'huun the Blood God's battlecry lets player draw 2 cards. Those cost Health instead of mana")
		card1 = self.Game.Hand_Deck.drawCard(self.ID)
		card2 = self.Game.Hand_Deck.drawCard(self.ID)
		if card1: card1.marks["Cost Health Instead"] = 1
		if card2: card2.marks["Cost Health Instead"] = 1
		return None
		
		
class BloodofGhuun(Minion):
	Class, race, name = "Priest", "Elemental", "Blood of G'huun"
	mana, attack, health = 9, 8, 8
	index = "Darkmoon~Priest~Minion~9~8~8~Elemental~Blood of G'huun~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. At the end of your turn, summon a 5/5 copy of a minion in your deck"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_BloodofGhuun(self)]
		
class Trig_BloodofGhuun(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnEnds"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		minion = self.entity
		curGame = minion.Game
		if curGame.mode == 0:
			PRINT(curGame, "At the end of turn, Blood of G'huun summons a 5/5 copy of a minion in played's deck")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[minion.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions and curGame.space(minion.ID) > 0 else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				Copy = curGame.Hand_Deck.decks[minion.ID][i].selfCopy(minion.ID, 5, 5)
				curGame.summon(Copy, minion.position+1, minion.ID)
			
"""Rogue cards"""
class PrizePlunderer(Minion):
	Class, race, name = "Rogue", "Pirate", "Prize Plunderer"
	mana, attack, health = 1, 2, 1
	index = "Darkmoon~Rogue~Minion~1~2~1~Pirate~Prize Plunderer~Combo"
	requireTarget, keyWord, description = True, "", "Combo: Deal 1 damage to a minion for each other card you've played this turn"
	
	def returnTrue(self, choice=0):
		return self.Game.Counters.numCardsPlayedThisTurn[self.ID] > 0
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target != self and target.onBoard
		
	def effectCanTrigger(self):
		self.effectViable = self.Game.Counters.numCardsPlayedThisTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		numOtherCards = self.Game.Counters.numCardsPlayedThisTurn[self.ID]
		if target and numOtherCards > 0:
			PRINT(self.Game, "Prize Plunderer's Combo triggers and deals %d damage to minion %s"%(numOtherCards, target.name))
			self.dealsDamage(target, numOtherCards)
		return target
		
		
class FoxyFraud(Minion):
	Class, race, name = "Rogue", "", "Foxy Fraud"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Rogue~Minion~2~3~2~None~Foxy Fraud~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Your next Combo this turn costs (2) less"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Foxy Fraud's battlecry makes player's next Combo this turn cost (2) less.")
		tempAura = YourNextComboCosts2LessThisTurn(self.Game, self.ID)
		self.Game.Manas.CardAuras.append(tempAura)
		tempAura.auraAppears()
		return None
		
class YourNextComboCosts2LessThisTurn(TempManaEffect):
	def __init__(self, Game, ID):
		self.Game, self.ID = Game, ID
		self.changeby, self.changeto = -2, -1
		self.temporary = True
		self.auraAffected = []
		
	def applicable(self, target):
		return target.ID == self.ID and "~Combo" in target.index
		
	def selfCopy(self, game):
		return type(self)(game, self.ID)
		
		
class ShadowClone(Secret):
	Class, name = "Rogue", "Shadow Clone"
	requireTarget, mana = False, 2
	index = "Darkmoon~Rogue~Spell~2~Shadow Clone~~Secret"
	description = "Secret: After a minion attacks your hero, summon a copy of it with Stealth"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_ShadowClone(self)]
		
class Trig_ShadowClone(SecretTrigger):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAttackedHero"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.ID != self.entity.Game.turn and target == self.entity.Game.heroes[self.entity.ID]
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "After a minion %s attacks player, Secret Shadow Clone is triggered and summons a copy of it with Stealth"%subject.name)
		Copy = subject.selfCopy(self.entity.ID)
		self.entity.Game.summon(Copy, -1, self.entity.ID)
		
		
class SweetTooth(Minion):
	Class, race, name = "Rogue", "", "Sweet Tooth"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Rogue~Minion~2~3~2~None~Sweet Tooth"
	requireTarget, keyWord, description = False, "", "Corrupt: Gain +2 Attack and Stealth"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, SweetTooth_Corrupt)] #只有在手牌中才会升级
		
class SweetTooth_Corrupt(Minion):
	Class, race, name = "Rogue", "", "Sweet Tooth"
	mana, attack, health = 2, 5, 2
	index = "Darkmoon~Priest~Minion~2~5~2~None~Sweet Tooth~Stealth~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "Stealth", "Corrupted. Stealth"
	
	
class Swindle(Spell):
	Class, name = "Rogue", "Swindle"
	requireTarget, mana = False, 2
	index = "Darkmoon~Rogue~Spell~2~Swindle"
	description = "Draw a spell. Combo: And a minion"
	def effectCanTrigger(self):
		self.effectViable = self.Game.Counters.numCardsPlayedThisTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		canTrig = curGame.Counters.numCardsPlayedThisTurn[self.ID] > 0
		if canTrig:
			typeCards = ["Spell", "Minion"]
			PRINT(self.Game, "Swindle's Combo triggers and lets player draw a spell and a minion")
		else:
			typeCards = ["Spell"]
			PRINT(self.Game, "Swindle lets player draw a spell")
		if curGame.mode == 0:
			for typeCard in typeCards:
				if curGame.guides:
					i = curGame.guides.pop(0)
				else:
					cards = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == typeCard]
					i = npchoice(cards) if cards else -1
					curGame.fixedGuides.append(i)
				if i > -1: curGame.Hand_Deck.drawCard(self.ID, i)[0]
		return None
		
		
class TenwuoftheRedSmoke(Minion):
	Class, race, name = "Rogue", "", "Tenwu of the Red Smoke"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Rogue~Minion~2~3~2~None~Tenwu of the Red Smoke~Battlecry~Legendary"
	requireTarget, keyWord, description = True, "", "Battlecry: Return a friendly minion to you hand. It costs (1) less this turn"
	
	def targetExists(self, choice=0):
		return self.selectableFriendlyMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.ID == self.ID and target != self and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target and target.onBoard:
			PRINT(self.Game, "Tenwu of the Red Smoke's battlecry returns friendly minion %s to player's hand."%target.name)
			self#.Game.returnMiniontoHand(target)
		return target
		
		
class CloakofShadows(Spell):
	Class, name = "Rogue", "Cloak of Shadows"
	requireTarget, mana = False, 3
	index = "Darkmoon~Rogue~Spell~3~Cloak of Shadows"
	description = "Give your hero Stealth for 1 turn"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Cloak of Shadows gives player's Hero Stealth for 1 turn")
		self.Game.heroes[self.ID].status["Temp Stealth"] += 1
		return None
		
		
class TicketMaster(Minion):
	Class, race, name = "Rogue", "", "Ticket Master"
	mana, attack, health = 3, 4, 3
	index = "Darkmoon~Rogue~Minion~3~4~3~None~Ticket Master~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Shuffle 3 Tickets into your deck. When drawn, summon a 3/3 Plush Bear"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Ticket Master's battlecry shuffles 3 Tickets into player's deck. When its drawn, it summons a 3/3 Plush Bear.")
		self.Game.Hand_Deck.shuffleCardintoDeck([Tickets(self.Game, self.ID) for i in range(3)], self.ID)
		return None
		
class Tickets(Spell):
	Class, name = "Rogue", "Tickets"
	requireTarget, mana = False, 3
	index = "Darkmoon~Rogue~Spell~3~Tickets~Casts When Drawn~Uncollectible"
	description = "Casts When Drawn. Summon a 3/3 Plush Bear"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Tickets is cast and summon a 3/3 Plush Bear")
		self.Game.summon(PlushBear(self.Game, self.ID), -1, self.ID)
		return None
		
class PlushBear(Minion):
	Class, race, name = "Rogue", "", "Plush Bear"
	mana, attack, health = 3, 3, 3
	index = "Darkmoon~Rogue~Minion~3~3~3~None~Plush Bear~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
	
class MalevolentStrike(Minion):
	Class, name = "Rogue", "Malevolent Strike"
	requireTarget, mana = True, 5
	index = "Darkmoon~Rogue~Spell~5~Malevolent Strike"
	description = "Destroy a minion. Costs (1) less for each card in your deck that didn't start there"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_MalevolentStrike(self)]
		
	def selfManaChange(self):
		if self.inHand:
			num = 
			self.mana -= num
			self.mana = max(0, self.mana)
		
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard:
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			PRINT(self.Game, "Malevolent Strike destroys minion %s"%target.name)
			self.Game.killMinion(self, target)
		return target
		
class Trig_MalevolentStrike(TrigHand):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAppears", "MinionDisappears"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Manas.calcMana_Single(self.entity)
	
	
class GrandEmpressShekzara(Minion):
	Class, race, name = "Rogue", "", "Grand Empress Shek'zara"
	mana, attack, health = 6, 5, 7
	index = "Darkmoon~Rogue~Minion~6~5~7~None~Grand Empress Shek'zara~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Discover a card in your deck and draw all copies of it"
	
	def drawCopiesofIndex(self, info): #info is the index of the card in player's deck
		ownDeck = self.Game.Hand_Deck.decks[self.ID]
		copytoDraw = type(ownDeck[info])
		#Assume draw from the top of the deck and milling is possible
		indices = [i for i, card in enumerate(ownDeck) if type(card) == copytoDraw]
		for i in reversed(indices):
			self.Game.Hand_Deck.drawCard(self.ID, i)
			
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		numCardsLeft = len(curGame.Hand_Deck.decks[self.ID])
		if numCardsLeft == 1:
			PRINT(curGame, "Grand Empress Shek'zara's battlecry lets player draw the only card in deck")
			curGame.Hand_Deck.drawCard(self.ID)
		elif numCardsLeft > 1 and self.ID == curGame.turn:
			if curGame.mode == 0:
				if curGame.guides:
					PRINT(curGame, "Grand Empress Shek'zara's battlecry lets player")
					GrandEmpressShekzara.drawCopiesofIndex(self, curGame.guides.pop(0))
				else:
					cards, cardTypes = [], []
					for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]):
						if type(card) not in cardTypes:
							cards.append(i)
							cardTypes.append(type(card))
					if "byOthers" in comment:
						i = npchoice(cards)
						curGame.fixedGuides.append(i)
						PRINT(curGame, "Grand Empress Shek'zara's battlecry lets player draw the copies of a random card from player's deck")
						GrandEmpressShekzara.drawCopiesofIndex(self, i)
					else:
						PRINT(curGame, "Grand Empress Shek'zara's battlecry lets player discover copies of a card to draw from deck")
						indices = npchoice(cards, min(3, len(cards)), replace=False)
						curGame.options = [curGame.Hand_Deck.decks[self.ID][i] for i in indices]
						curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		for i, card in enumerate(self.Game.Hand_Deck.decks[self.ID]):
			if isinstance(card, type(option)):
				self.Game.fixedGuides.append(i)
				break
		GrandEmpressShekzara.drawCopiesofIndex(self, i)
		
		
"""Shaman cards"""
class Revolve(Spell):
	Class, name = "Shaman", "Revolve"
	requireTarget, mana = False, 1
	index = "Darkmoon~Shaman~Spell~1~Revolve"
	description = "Transform all minions into random ones with the same Cost"
	poolIdentifier = "1-Cost Minions to Summon"
	@classmethod
	def generatePool(cls, Game):
		return ["%d-Cost Minions to Summon"%cost for cost in Game.MinionsofCost.keys()], \
				[list(Game.MinionsofCost[cost].values()) for cost in Game.MinionsofCost.keys()]
				
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Revolve transforms all minions into random ones with the same Cost")
			minions = curGame.minionsonBoard(1) + curGame.minionsonBoard(2)
			if curGame.guides:
				newMinions = curGame.guides.pop(0)
			else:
				newMinions = [npchoice(curGame.RNGPools["%d-Cost Minions to Summon"%minion.mana]) for minion in minions]
				curGame.fixedGuides.append(tuple(newMinions))
			for minion, newMinion in zip(minions, newMinions):
				curGame.transform(minion, newMinion(curGame, minion.ID))
		return None
		
		
class CagematchCustodian(Minion):
	Class, race, name = "Shaman", "Elemental", "Cagematch Custodian"
	mana, attack, health = 2, 2, 2
	index = "Darkmoon~Shaman~Minion~2~2~2~Elemental~Cagematch Custodian~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Draw a weapon"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Cagematch Custodian's battlecry lets player draw a weapon")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				cards = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Weapon"]
				i = npchoice(cards) if cards else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.Hand_Deck.drawCard(self.ID, i)[0]
		return None
		
		
class DeathmatchPavilion(Spell):
	Class, name = "Shaman", "Deathmatch Pavilion"
	requireTarget, mana = False, 2
	index = "Darkmoon~Shaman~Spell~2~Deathmatch Pavilion"
	description = "Summon a 3/2 Duelist. If your hero attacked this turn, summon another"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def effectCanTrigger(self):
		self.effectViable = self.Game.Counters.heroAttackTimesThisTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Deathmatch Pavilion summons a 3/2 Duelist")
		curGame.summon(PavilionDuelist(curGame, self.ID), -1, self.ID)
		if curGame.Counters.heroAttackTimesThisTurn[self.ID] > 0
			PRINT(curGame, "As player attacked this turn, Deathmatch Pavilion summons another 3/2 Duelist")
			curGame.summon(PavilionDuelist(curGame, self.ID), -1, self.ID)
		return None
		
class PavilionDuelist(Minion):
	Class, race, name = "Shaman", "", "Pavilion Duelist"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Shaman~Minion~2~3~2~None~Pavilion Duelist~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
	
class GrandTotemEysor(Minion):
	Class, race, name = "Shaman", "Totem", "Grand Totem Eys'or"
	mana, attack, health = 3, 0, 4
	index = "Darkmoon~Shaman~Minion~3~0~4~Totem~Grand Totem Eys'or~Legendary"
	requireTarget, keyWord, description = False, "", "At the end of your turn, give +1/+1 to all other Totems in your hand, deck and battlefield"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_GrandTotemEysor(self)]
		
class Trig_GrandTotemEysor(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnEnds"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame, side = self.entity.Game, self.entity.ID
		PRINT(curGame, "At the end of turn, Master Swordsmith gvies another random friendly minion %s +1 Attack."%minion.name)
		for obj in curGame.minionsonBoard(side):
			if "Totem" in obj.race and obj != self.entity:
				obj.buffDebuff(1, 1)
		for card in curGame.Hand_Deck.hands[side] + curGame.Hand_Deck.decks[side]:
			if obj.type == "Minion" and "Totem" in obj.race:
				obj.buffDebuff(1, 1)
				
				
class Magicfin(Minion):
	Class, race, name = "Shaman", "Murloc", "Magicfin"
	mana, attack, health = 3, 3, 4
	index = "Darkmoon~Shaman~Minion~3~3~4~Murloc~Magicfin"
	requireTarget, keyWord, description = False, "", "After a friendly Murloc dies, add a random Legendary minion to your hand"
	poolIdentifier = "Legendary Minions"
	@classmethod
	def generatePool(cls, Game):
		return "Legendary Minions", list(Game.LegendaryMinions.values())
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_Magicfin(self)]
		
class Trig_Magicfin(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionDies"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and target != self.entity and target.ID == self.entity.ID and "Murloc" in target.race #Technically, minion has to disappear before dies. But just in case.
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "A friendly Murloc %s dies and Magicfin adds a random Legendary minion to player's hand."%target.name)
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				minion = npchoice(curGame.RNGPools["Legendary Minions"])
				curGame.fixedGuides.append(minion)
			curGame.Hand_Deck.addCardtoHand(minion, self.entity.ID, "type")
			
			
class PitMaster(Minion):
	Class, race, name = "Shaman", "", "Pit Master"
	mana, attack, health = 3, 1, 2
	index = "Darkmoon~Shaman~Minion~3~1~2~None~Pit Master~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Summon a 3/2 Duelist. Corrupt: Summon two"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, PitMaster_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Pit Master's battlecry summons a 3/2 Duelist")
		self.Game.summon(PavilionDuelist(self.Game, self.ID), self.position+1, self.ID)
		return None
		
class PitMaster_Corrupt(Minion):
	Class, race, name = "Shaman", "", "Pit Master"
	mana, attack, health = 3, 1, 2
	index = "Darkmoon~Shaman~Minion~3~1~2~None~Pit Master~Battlecry~Corrupted~Uncollectible"
	requireTarget, keyWord, description = False, "", "Corrupted. Battlecry: Summon two 3/2 Duelists"
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Pit Master's battlecry summons two 3/2 Duelists")
		pos = (self.position, "leftandRight") if self.onBoard else (-1, "totheRightEnd")
		self.Game.summon([PavilionDuelist(self.Game, self.ID) for i in range(2)], pos, self.ID)
		return None
		
		
class Stormstrike(Spell):
	Class, name = "Shaman", "Stormstrike"
	requireTarget, mana = True, 3
	index = "Darkmoon~Shaman~Spell~3~Stormstrike"
	description = "Deal 3 damage to a minion. Give your hero +3 Attack this turn"
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			damage = (3 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Stormstrike deals %d damage to minion %s. Then gives player +3 Attack this turn"%(damage, target.name))
			self.dealsDamage(target, damage)
			self.Game.heroes[self.ID].gainAttack(3)
		return target
		
		
class WhackaGnollHammer(Weapon):
	Class, name, description = "Shaman", "Whack-a-Gnoll Hammer", "After your hero attacks, give a random friendly minion +1/+1"
	mana, attack, durability = 3, 3, 2
	index = "Darkmoon~Shaman~Weapon~3~3~2~Whack-a-Gnoll Hammer"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_WhackaGnollHammer(self)]
		
class Trig_WhackaGnollHammer(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["HeroAttackedMinion", "HeroAttackedHero"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject == self.entity.Game.heroes[self.entity.ID] and self.entity.onBoard
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		PRINT(curGame, "After player attacks, weapon  gives a random friendly minion +1/+1")
		if curGame.mode == 0:
			if curGame.guides:
				i, where = curGame.guidies.pop(0)
			else:
				minions = curGame.minionsonBoard(self.entity.ID)
				i = npchoice(minions).position if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.minions[self.entity.ID][i].buffDebuff(1, 1)
			
			
class DunkTank(Spell):
	Class, name = "Shaman", "Dunk Tank"
	requireTarget, mana = True, 4
	index = "Darkmoon~Shaman~Spell~4~Dunk Tank"
	description = "Deal 4 damage. Corrupt: Then deal 2 damage to all enemy minions"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, DunkTank_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			damage = (4 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Dunk Tank deals %d damage to %s"%(damage, target.name))
			self.dealsDamage(target, damage)
		return target
		
class DunkTank_Corrupt(Spell):
	Class, name = "Shaman", "Dunk Tank"
	requireTarget, mana = True, 4
	index = "Darkmoon~Shaman~Spell~4~Dunk Tank~Corrupted~Uncollectible"
	description = "Corrupted. Deal 4 damage. Then deal 2 damage to all enemy minions"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			damage_4 = (4 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Dunk Tank deals %d damage to %s"%(damage_4, target.name))
			self.dealsDamage(target, damage_4)
			damage_2 = (2 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
			PRINT(self.Game, "Dunk Tank deals %d damage to all enemy minions"%damage_2)
			minions = self.Game.minionsonBoard(3-self.ID)
			self.dealsAOE(minions, [damage_2] * len(minions))
		return target
		
		
class InaraStormcrash(Minion):
	Class, race, name = "Shaman", "", "Inara Stormcrash"
	mana, attack, health = 5, 4, 5
	index = "Darkmoon~Shaman~Minion~5~4~5~None~Inara Stormcrash~Legendary"
	requireTarget, keyWord, description = False, "", "On your turn, your hero has +2 Attack and Windfury"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.auras["Mana Aura"] = ManaAura_Dealer(self, changeby=0, changeto=-1)
		self.trigsBoard = [Trig_GameMaster(self)]
		
	def manaAuraApplicable(self, target):
		return target.ID == self.ID and target.description.startswith("Secret:")
		
	def checkAuraCorrectness(self): #负责光环在随从登场时无条件启动之后的检测。如果光环的启动条件并没有达成，则关掉光环
		if self.Game.turn != self.ID or any(index.endswith("~~Secret") for index in self.Game.Counters.cardsPlayedThisTurn[self.ID]["Indices"]):
			self.auras["Mana Aura"].auraDisappears()
			
	def deactivateAura(self): #随从被沉默时优先触发disappearResponse,提前关闭光环，之后auraDisappears可以再调用一次，但是没有作用而已
		self.auras["Mana Aura"].auraDisappears()
		
class HeroBuffAura_InaraStormcrash:
	def __init__(self, entity):
		self.entity = entity
		self.auraAffected = []
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and ("Turn" in signal or subject.ID == minion.ID)
		
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			self.effect(signal, ID, subject, target, number, comment)
			
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		minion = self.entity
		if "Turn" in signal: #
			if ID == minion.ID:
				if minion.Game.heroes[ID] not in self.auraAffected:
					self.applies(minion.Game.heroes[ID])
			else:
				for hero, aura_Receiver in fixedList(self.auraAffected):
					aura_Receiver.effectClear()
				self.auraAffected = []
		elif minion.ID == minion.Game.turn: #During your turn, new hero on board will receive the aura for sure
			self.applies(subject)
			
	def applies(self, subject):
		HeroBuffAura_Receiver(subject, self).effectStart()
		HeroWindfuryAura_Receiver(subject, self).effectStart()
		
	def auraAppears(self):
		curGame, ID = self.entity.Game, self.entity.ID
		if curGame.turn == ID:
			if curGame.heroes[ID] not in self.auraAffected:
				self.applies(curGame.heroes[ID])
		trigsBoard = curGame.trigsBoard[ID]
		for sig in ["HeroReplaced", "TurnStarts", "TurnEnds"]:
			try: trigsBoard[sig].append(self)
			except: trigsBoard[sig] = [self]
			
	def auraDisappears(self):
		for hero, aura_Receiver in fixedList(self.auraAffected):
			aura_Receiver.effectClear()
		self.auraAffected = []
		trigsBoard = curGame.trigsBoard[self.entity.ID]
		for sig in ["HeroReplaced", "TurnStarts", "TurnEnds"]:
			try: trigsBoard[sig].remove(self)
			except: pass
			
	def selfCopy(self, recipient):
		return type(self)(recipient)
		
	#这个函数会在复制场上扳机列表的时候被调用。
	def createCopy(self, game):
		#一个光环的注册可能需要注册多个扳机
		if self not in game.copiedObjs: #这个光环没有被复制过
			entityCopy = self.entity.createCopy(game)
			Copy = self.selfCopy(entityCopy)
			game.copiedObjs[self] = Copy
			for entity, aura_Receiver in self.auraAffected:
				entityCopy = entity.createCopy(game)
				#武器光环的statbyAura是[0, []]
				receiverIndex = entity.statbyAura[1].index(aura_Receiver)
				receiverCopy = entityCopy.statbyAura[1][receiverIndex]
				receiverCopy.source = Copy #补上这个receiver的source
				Copy.auraAffected.append((entityCopy, receiverCopy))
			return Copy
		else:
			return game.copiedObjs[self]
			
			
"""Warlock cards"""
class WickedWhispers(Spell):
	Class, name = "Warlock", "Wicked Whispers"
	requireTarget, mana = False, 1
	index = "Darkmoon~Warlock~Spell~1~Wicked Whispers"
	description = "Discard your lowest Cost card. Give your minions +1/+1"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Wicked Whispers discards the lowest Cost card in player's hand and gives player's minions +1/+1.")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				cards, lowestCost = [], np.inf
				for i, card in enumerate(curGame.Hand_Deck.hands[self.ID]):
					if card.mana < lowestCost: cards, lowestCost = [i], card.mana
					elif card.mana == lowestCost: cards.append(i)
				i = npchoice(cards) if cards else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.Hand_Deck.discardCard(self.ID, i)
			for minion in curGame.minionsonBoard(self.ID):
				minion.buffDebuff(1, 1)
		return None
		
		
class MidwayManiac(Minion):
	Class, race, name = "Warlock", "Demon", "Midway Maniac"
	mana, attack, health = 2, 1, 5
	index = "Darkmoon~Warlock~Minion~2~1~5~Demon~Midway Maniac~Taunt"
	requireTarget, keyWord, description = False, "Taunt", "Taunt"
	
	
class FreeAdmission(Spell):
	Class, name = "Warlock", "Free Admission"
	requireTarget, mana = False, 3
	index = "Darkmoon~Warlock~Spell~3~Free Admission"
	description = "Draw 2 minions. If they're both Demons, reduce their Cost by (2)"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		PRINT(curGame, "Free Admission lets player draw two minions.")
		cards = [None, None]
		if curGame.mode == 0:
		for num in range(2):
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.entity.ID]) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				cards[num] = curGame.Hand_Deck.drawCard(self.entity.ID, i)[0]
		if cards[0] and "Demon" in cards[0].race and cards[1] and "Demon" in cards[1].race:
			PRINT(curGame, "Both minions drawn are Demons. Free Admission reduce their Cost by (2)")
			ManaMod(cards[0], changeby=-2, changeto=-1).applies()
			ManaMod(cards[1], changeby=-2, changeto=-1).applies()
			
			
class ManariMosher(Minion):
	Class, race, name = "Warlock", "Demon", "Man'ari Mosher"
	mana, attack, health = 3, 3, 4
	index = "Darkmoon~Warlock~Minion~3~3~4~Demon~Man'ari Mosher~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Give a friendly Demon +3 Attack and Lifesteal this turn"
	def targetExists(self, choice=0):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target != self and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target and (target.onBoard or target.inHand):
			PRINT(self.Game, "Man'ari Mosher's battlecry gives friendly Demon %s +3 attack and Lifesteal this turn."%target.name)
			target.buffDebuff(3, 0, "EndofTurn")
			target.getsKeyword("Lifesteal")
			trig = Trig_ManariMosher(target)
			target.
			trig.connect()
		return target
		
class Trig_ManariMosher:
	def __init__(self, entity):
		self.entity, self.signals, self.temp = entity, ["TurnStarts", "TurnEnds"], False
		
	def connect(self):
		if self.entity.onBoard: trigs = self.entity.Game.trigsBoard[self.entity.ID]
		else: trigs = self.entity.Game.trigsHand[self.entity.ID]
		for sig in self.signals:
			try: trigs[sig].append(self)
			except: trigs[self.entity.ID][sig] = [self]
			
	def disconnect(self):
		for sig in self.signals:
			try: self.entity.Game.trigsHand[self.entity.ID][sig].remove(self)
			except: pass
			try: self.entity.Game.trigsBoard[self.entity.ID][sig].remove(self)
			except: pass
			
	def trigger(self, signal, ID, subject, target, number, comment, choice=0):
		if self.canTrigger(signal, ID, subject, target, number, comment):
			if self.entity.Game.GUI: self.entity.Game.GUI.triggerBlink(self.entity)
			self.effect(signal, ID, subject, target, number, comment)
			
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return True #This triggers at either player's turn end and start
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		minion = self.entity
		minion.losesKeyword("Lifesteal")
		for sig in self.signals:
			try: minion.Game.trigsHand[minion.ID][sig].remove(self)
			except: pass
			try: minion.Game.trigsBoard[minion.ID][sig].remove(self)
			except: pass
		try: minion.trigsBoard.remove(self)
		except: pass
		try: minion.trigsHand.remove(self)
		except: pass
		
	def selfCopy(self, recipient):
		return type(self)(recipient)
		
	def createCopy(self, game):
		if self not in game.copiedObjs: #这个扳机没有被复制过
			entityCopy = self.entity.createCopy(game)
			trigCopy = type(self)(entityCopy)
			game.copiedObjs[self] = trigCopy
			return trigCopy
		else: #一个扳机被复制过了，则其携带者也被复制过了
			return game.copiedObjs[self]
			
			
class CascadingDisaster(Spell):
	Class, name = "Warlock", "Cascading Disaster"
	requireTarget, mana = False, 4
	index = "Darkmoon~Warlock~Spell~4~Cascading Disaster"
	description = "Destroy a random enemy minion. Corrupt: Destroy 2. Corrupt Again: Destroy 3"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, CascadingDisaster_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		curGame = self.Game
		PRINT(curGame, "Cascading Disaster destroys a random enemy minion")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = curGame.minionsAlive(3-self.ID)
				i = npchoice(minions).position if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				self.Game.killMinion(self, curGame.minions[3-self.ID][i])
		return None
		
class CascadingDisaster_Corrupt(Spell):
	Class, name = "Warlock", "Cascading Disaster"
	requireTarget, mana = False, 4
	index = "Darkmoon~Warlock~Spell~4~Cascading Disaster~Corrupted~Uncollectible"
	description = "Corrupted. Destroy 2 random enemy minions. Corrupt: Destroy 3"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, CascadingDisaster_Corrupt2)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		curGame = self.Game
		PRINT(curGame, "Cascading Disaster destroys 2 random enemy minions")
		if curGame.mode == 0:
			if curGame.guides:
				minions = [curGame.minions[3-self.ID][i] for i in curGame.guides.pop(0)]
			else:
				minions = curGame.minionsAlive(3-self.ID)
				minions = npchoice(minions, min(2, len(minions), replace=False) if minions else ()
				indices = tuple(minion.position for minion in minions)
			for minion in minions: curGame.killMinion(self, minion)
		return None
		
class CascadingDisaster_Corrupt2(Spell):
	Class, name = "Warlock", "Cascading Disaster"
	requireTarget, mana = False, 4
	index = "Darkmoon~Warlock~Spell~4~Cascading Disaster~Corrupted2~Uncollectible"
	description = "Corrupted. Destroy 3 random enemy minions"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		curGame = self.Game
		PRINT(curGame, "Cascading Disaster destroys 3 random enemy minions")
		if curGame.mode == 0:
			if curGame.guides:
				minions = [curGame.minions[3-self.ID][i] for i in curGame.guides.pop(0)]
			else:
				minions = curGame.minionsAlive(3-self.ID)
				minions = npchoice(minions, min(3, len(minions), replace=False) if minions else ()
				indices = tuple(minion.position for minion in minions)
			for minion in minions: curGame.killMinion(self, minion)
		return None
		
		
class RevenantPascal(Minion):
	Class, race, name = "Warlock", "", "Revenant Pascal"
	mana, attack, health = 3, 3, 3
	index = "Darkmoon~Warlock~Minion~3~3~3~None~Revenant Pascal~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Destroy a Mana Crystal for both players"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Revenant Pascal's battlecry destroys a mana crystal for both players.")
		self.Game.Manas.destroyManaCrystal(1, self.ID)
		self.Game.Manas.destroyManaCrystal(2, self.ID)
		return None
		
		
class FireBreather(Minion):
	Class, race, name = "Warlock", "Demon", "Fire Breather"
	mana, attack, health = 4, 4, 3
	index = "Darkmoon~Warlock~Minion~4~4~3~Demon~Fire Breather~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Deal 2 damage to all minions except Demons"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		minions = [minion for minion in self.Game.minionsonBoard(1) + self.Game.minionsonBoard(2) if "Demon" not in minion.race]
		PRINT(self.Game, "Fire Breather's battlecry deals 2 damage to all minions except Demons")
		self.dealsAOE(minions, [2] * len(minions))
		return None
		
		
class DeckofChaos(Spell):
	Class, name = "Warlock", "Deck of Chaos"
	requireTarget, mana = False, 6
	index = "Darkmoon~Warlock~Spell~6~Deck of Chaos~Legendary"
	description = "Swap the Cost and Attack of all minions in your deck"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Deck of Chaos swaps the Cost and Attack of all minions in player's deck")
		for card in self.Game.Hand_Deck.decks[self.ID]:
			if card.type == "Minion":
				att = card.attack
				card.attack = card.mana
				for manaMod in reversed(card.manaMods): manaMod.getsRemoved()
				ManaMod(card, changeby=0, changeto=max(0, att)).applies()
		return None
		
		
class RingMatron(Minion):
	Class, race, name = "Warlock", "Demon", "Ring Matron"
	mana, attack, health = 6, 6, 4
	index = "Darkmoon~Warlock~Minion~6~6~4~Demon~Ring Matron~Taunt~Deathrattle"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Deathrattle: Summon two 3/2 Imps"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [SummonTwo32Imps(self)]
		
class SummonTwo32Imps(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		pos = (self.entity.position, "leftandRight") if self.entity in self.entity.Game.minions[self.entity.ID] else (-1, "totheRightEnd")
		PRINT(self.entity, "Deathrattle: Summon two 2/2 Hyenas triggers.")
		self.entity.Game.summon([FieryImp(self.entity.Game, self.entity.ID) for i in range(2)], pos, self.entity.ID)
		
class FieryImp(Minion):
	Class, race, name = "Warlock", "Demon", "Fiery Imp"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Warlock~Minion~2~3~2~Demon~Fiery Imp~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
	
class Tickatus(Minion):
	Class, race, name = "Warlock", "Demon", "Tickatus"
	mana, attack, health = 6, 8, 8
	index = "Darkmoon~Warlock~Minion~6~8~8~Demon~Tickatus~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Remove the top 5 cards from your deck. Corrupt: Your opponent's instead"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, Tickatus_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		PRINT(self.Game, "Tickatus' battlecry removes the top 5 cards from player's deck")
		self.Game.Hand_Deck.removeDeckTopCard(self.ID, num=5)
		return None
		
class Tickatus_Corrupt(Minion):
	Class, race, name = "Warlock", "Demon", "Tickatus"
	mana, attack, health = 6, 8, 8
	index = "Darkmoon~Warlock~Minion~6~8~8~Demon~Tickatus~Battlecry~Corrupted~Legendary~Uncollectible"
	requireTarget, keyWord, description = False, "", "Corrupted. Battlecry: Remove the top 5 cards from your opponent's deck"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		PRINT(self.Game, "Tickatus' battlecry removes the top 5 cards from the opponent's deck")
		self.Game.Hand_Deck.removeDeckTopCard(3-self.ID, num=5)
		return None
		
"""Warrior cards"""
class StageDive(Spell):
	Class, name = "Warrior", "Stage Dive"
	requireTarget, mana = False, 1
	index = "Darkmoon~Warrior~Spell~1~Stage Dive"
	description = "Draw a Rush minion. Corrupt: Give it +2/+1"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_Corrupt(self, StageDive_Corrupt)] #只有在手牌中才会升级
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Stage Dive lets player draw a Rush minion")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion" and card.keyWords["Rush"] > 0]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.Hand_Deck.drawCard(self.ID, i)
		return None
		
class StageDive_Corrupt(Spell):
	Class, name = "Warrior", "Stage Dive"
	requireTarget, mana = False, 1
	index = "Darkmoon~Warrior~Spell~1~Stage Dive~Corrupted~Uncollectible"
	description = "Corrupted. Draw a Rush minion and give it +2/+1"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			PRINT(curGame, "Stage Dive lets player draw a Rush minion and give it +2/+1")
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion" and card.keyWords["Rush"] > 0]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.Hand_Deck.drawCard(self.ID, i)[0]
				if minion: minion.buffDebuff(2, 1)
		return None
		
		
class BumperCar(Minion):
	Class, race, name = "Warrior", "Mech", "Bumper Car"
	mana, attack, health = 2, 1, 3
	index = "Darkmoon~Warrior~Minion~2~1~3~Mech~Bumper Car~Rush~Deathrattle"
	requireTarget, keyWord, description = False, "Rush", "Rush. Deathrattle: Add two 1/1 Riders with Rush to your hand"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [AddTwo11RiderstoYourHand(self)]
		
class AddTwo11RiderstoYourHand(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "Deathrattle: Add two 1/1 Riders with Rush to your hand triggers")
		self.entity.Game.Hand_Deck.addCardtoHand([DarkmoonRider, DarkmoonRider], self.entity.ID, "type")
		
		
class ETCGodofMetal(Minion):
	Class, race, name = "Warrior", "", "E.T.C., God of Metal"
	mana, attack, health = 2, 1, 4
	index = "Darkmoon~Warrior~Minion~2~1~4~None~E.T.C., God of Metal~Legendary"
	requireTarget, keyWord, description = False, "", "After a friendly Rush minion attack, deal 2 damage to the enemy hero"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_ETCGodofMetal(self)]
		
class Trig_ETCGodofMetal(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAttackedMinion", "MinionAttackedHero"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.entity.ID and subject.keyWords["Rush"] > 0 and self.entity.onBoard
		
	#不知道攻击具有受伤时召唤一个随从的扳机的随从时，飞刀能否对这个友方角色造成伤害
	#目前的写法是这个战斗结束信号触发在受伤之后
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		PRINT(self.entity.Game, "After friendly minion %s attacks, E.T.C., God of Metal deals 2 damage to the enemy hero"%subject.name)
		self.entity.dealsDamage(self.entity.Game.heroes[3-self.entity.ID], 2)
		
		
class Minefield(Spell):
	Class, name = "Warrior", "Minefield"
	requireTarget, mana = False, 2
	index = "Darkmoon~Warrior~Spell~2~Minefield"
	description = "Deal 5 damage randomly split among all minions"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		damage = (5 + self.countSpellDamage()) * (2 ** self.countDamageDouble())
		if curGame.mode == 0:
			PRINT(curGame, "Minefield deals %d damage randomly split among all minions."%damage)
			for num in range(damage):
				char = None
				if curGame.guides:
					i, where = curGame.guides.pop(0)
					if where: char = curGame.find(i, where)
				else:
					objs = curGame.minionsAlive(1) + curGame.minionsAlive(2)
					if objs:
						char = npchoice(objs)
						curGame.fixedGuides.append((char.position, char.type+str(char.ID)))
					else:
						curGame.fixedGuides.append((0, ''))
				if char:
					self.dealsDamage(char, 1)
				else: break
		return None
		
		
class RingmastersBaton(Weapon):
	Class, name, description = "Warrior", "Ringmaster's Baton", "After your hero attacks, give a Mech, Dragon, and Pirate in your hand +1/+1"
	mana, attack, durability = 2, 1, 3
	index = "Darkmoon~Warrior~Weapon~2~1~3~Ringmaster's Baton"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_RingmastersBaton(self)]
		
class Trig_RingmastersBaton(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["HeroAttackedMinion", "HeroAttackedHero"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return subject == self.entity.Game.heroes[self.entity.ID] and self.entity.onBoard
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		ownHand = curGame.Hand_Deck.hands[self.entity.ID]
		PRINT(curGame, "After player attacks, weapon Ringmaster's Baton gives a Mech, Dragon, and Pirate in player's hand +1/+1")
		if curGame.mode == 0:
			if curGame.guides:
				i, j, k = curGame.guidies.pop(0)
			else:
				mechs = [i for i, card in enumerate(ownHand) if card.type == "Minion" and "Mech" in card.race]
				dragons = [i for i, card in enumerate(ownHand) if card.type == "Minion" and "Dragon" in card.race]
				pirates = [i for i, card in enumerate(ownHand) if card.type == "Minion" and "Pirate" in card.race]
				i = npchoice(mechs) if mechs else -1
				j = npchoice(dragons) if dragons else -1
				k = npchoice(pirates) if pirates else -1
				curGame.fixedGuides.append((i, j, k))
			if i + j + k > -3:
				PRINT(curGame, "Ringmaster's Baton gives a Mech, Dragon, and Pirate in player's hand +1/+1")
				ownHand[i].buffDebuff(1, 1)
				ownHand[j].buffDebuff(1, 1)
				ownHand[k].buffDebuff(1, 1)
				
				
class StageHand(Minion):
	Class, race, name = "Warrior", "Mech", "Stage Hand"
	mana, attack, health = 2, 3, 2
	index = "Darkmoon~Warrior~Minion~2~3~2~Mech~Stage Hand~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Give a random minion in your hand +1/+1"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		ownHand = curGame.Hand_Deck.hands[self.ID]
		PRINT(curGame, "Stage Hand's battlecry gives a random minion in players hand +1/+1")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(ownHand) if card.type == "Minion"]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1: ownHand[i].buffDebuff(1, 1)
		return None
		
		
class FeatofStrength(Spell):
	Class, name = "Warrior", "Feat of Strength"
	requireTarget, mana = False, 3
	index = "Darkmoon~Warrior~Spell~3~Feat of Strength"
	description = "Give a random Taunt minion in your hand +5/+5"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		ownHand = curGame.Hand_Deck.hands[self.ID]
		PRINT(curGame, "Feat of Strength gives a random Taunt minion in players hand +5/+5")
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(ownHand) if card.type == "Minion" and card.keyWords["Taunt"] > 0]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1: ownHand[i].buffDebuff(5, 5)
		return None
		
		
class SwordEater(Minion):
	Class, race, name = "Warrior", "Pirate", "Sword Eater"
	mana, attack, health = 4, 2, 5
	index = "Darkmoon~Warrior~Minion~4~2~5~Pirate~Sword Eater~Taunt~Battlecry"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Battlecry: Equip a 3/2 Sword"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		PRINT(self.Game, "Sword Eater's battlecry equips a 3/2 Sword for player")
		self.Game.equipWeapon(Jawbreaker(self.Game, self.ID))
		return None
		
class Jawbreaker(Weapon):
	Class, name, description = "Warrior", "Jawbreaker", ""
	mana, attack, durability = 3, 3, 2
	index = "Darkmoon~Warrior~Weapon~3~3~2~Jawbreaker~Uncollectible"
	
	
class RingmasterWhatley(Minion):
	Class, race, name = "Warrior", "", "Ringmaster Whatley"
	mana, attack, health = 5, 3, 5
	index = "Darkmoon~Warrior~Minion~5~3~5~None~Ringmaster Whatley~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "", "Battlecry: Draw a Mech, Dragon, and Pirate"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=0):
		curGame = self.Game
		PRINT(curGame, "Ringmaster Whatley's battlecry lets player draw a Mech, Dragon, and Pirate")
		if curGame.mode == 0:
			for num in range(3):
				if curGame.guides:
					i = curGame.guides.pop(0)
				else:
					race = {0: "Mech", 1: "Dragon", 2: "Pirate"}[i]
					minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.type == "Minion" and race in card.race]
					i = npchoice(minions) if minions else -1
					curGame.fixedGuides.append(i)
				if i > -1: curGame.Hand_Deck.drawCard(self.ID, i)
		return None
		
		
class TentThrasher(Minion):
	Class, race, name = "Warrior", "Dragon", "Tent Thrasher"
	mana, attack, health = 5, 5, 5
	index = "Darkmoon~Warrior~Minion~5~5~5~Dragon~Tent Thrasher~Rush"
	requireTarget, keyWord, description = False, "Rush", "Rush. Costs (1) less for each friendly minion with a unique minion type"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_TentThrasher(self)]
		
	def selfManaChange(self):
		if self.inHand:
			races = cnt([minion.race for minion in self.Game.minionsonBoard(self.ID)])
			del races[""]
			#del races["Elemental,Mech,Demon,Murloc,Dragon,Beast,Pirate,Totem"]
			self.mana -= sum(value > 0 for value in races.values())
			self.mana = max(0, self.mana)
			
class Trig_TentThrasher(TrigHand):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAppears", "MinionDisappears"])
		
	def canTrigger(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand and ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Manas.calcMana_Single(self.entity)
		
		
Darkmoon_Indices = {"Darkmoon~Neutral~Minion~1~1~3~None~Safety Inspector~Battlecry": SafetyInspector,
					"Darkmoon~Neutral~Minion~2~1~2~None~Costumed Entertainer~Battlecry": CostumedEntertainer,
					"Darkmoon~Neutral~Minion~2~2~2~None~Horrendous Growth": HorrendousGrowth,
					"Darkmoon~Neutral~Minion~2~2~2~None~Horrendous Growth~Corrupted~Uncollectible": HorrendousGrowth_Corrupted_Mutable_3,
					"Darkmoon~Neutral~Minion~2~2~2~None~Parade Leader": ParadeLeader,
					"Darkmoon~Neutral~Minion~2~2~3~Murloc~Prize Vendor~Battlecry": PrizeVendor,
					"Darkmoon~Neutral~Minion~2~5~1~Elemental~Rock Rager~Taunt": RockRager,
					"Darkmoon~Neutral~Minion~2~3~2~None~Showstopper~Deathrattle": Showstopper,
					"Darkmoon~Neutral~Minion~2~2~1~None~Wriggling Horror~Battlecry": WrigglingHorror,
					"Darkmoon~Neutral~Minion~3~2~4~None~Banana Vendor~Battlecry": BananaVendor,
					"Darkmoon~Neutral~Spell~1~Bananas~Uncollectible": Bananas_Darkmoon,
					"Darkmoon~Neutral~Minion~3~3~2~Mech~Darkmoon Dirigible~Divine Shield": DarkmoonDirigible,
					"Darkmoon~Neutral~Minion~3~3~2~Mech~Darkmoon Dirigible~Divine Shield~Rush~Corrupted~Uncollectible": DarkmoonDirigible_Corrupted,
					"Darkmoon~Neutral~Minion~3~0~5~None~Darkmoon Statue": DarkmoonStatue,
					"Darkmoon~Neutral~Minion~3~4~5~None~Darkmoon Statue~Corrupted~Uncollectible": DarkmoonStatue_Corrupted,
					"Darkmoon~Neutral~Minion~3~3~2~Elemental~Gyreworm~Battlecry": Gyreworm,
					"Darkmoon~Neutral~Minion~3~2~2~None~Inconspicuous Rider~Battlecry": InconspicuousRider,
					"Darkmoon~Neutral~Minion~3~4~4~None~K'thir Ritualist~Taunt~Battlecry": KthirRitualist,
					"Darkmoon~Neutral~Minion~4~4~5~Elemental,Mech,Demon,Murloc,Dragon,Beast,Pirate,Totem~Circus Amalgam~Taunt": CircusAmalgam,
					"Darkmoon~Neutral~Minion~4~3~4~None~Circus Medic~Battlecry": CircusMedic,
					"Darkmoon~Neutral~Minion~4~3~4~None~Circus Medic~Battlecry~Corrupted~Uncollectible": CircusMedic_Corrupted,
					"Darkmoon~Neutral~Minion~4~3~5~Elemental~Fantastic Firebird~Windfury": FantasticFirebird,
					"Darkmoon~Neutral~Minion~4~3~4~None~Knife Vendor~Battlecry": KnifeVendor,
					"Darkmoon~Neutral~Minion~5~3~2~None~Derailed Coaster~Battlecry": DerailedCoaster,
					"Darkmoon~Neutral~Minion~1~1~1~None~Rider~Rush~Uncollectible": ,
					"Darkmoon~Neutral~Minion~5~4~4~Beast~Fleethoof Pearltusk~Rush": FleethoofPearltusk,
					"Darkmoon~Neutral~Minion~5~8~8~Beast~Fleethoof Pearltusk~Rush~Corrupted~Uncollectible": FleethoofPearltusk_Corrupted,
					"Darkmoon~Neutral~5~6~7~Minion~None~Optimistic Ogre": OptimisticOgre,
					"Darkmoon~Neutral~Minion~6~6~3~Mech~Claw Machine~Rush~Deathrattle": ClawMachine,
					"Darkmoon~Neutral~Minion~7~6~6~None~Strongman~Taunt": Strongman,
					"Darkmoon~Neutral~Minion~0~6~6~None~Strongman~Taunt~Corrupted~Uncollectible": Strongman_Corrupt,
					"Darkmoon~Neutral~Minion~9~4~4~None~Carnival Clown~Taunt~Battlecry": CarnivalClown,
					"Darkmoon~Neutral~Minion~9~4~4~None~Carnival Clown~Taunt~Battlecry~Corrupted~Uncollectible": CarnivalClown_Corrupt,
					"Darkmoon~Neutral~Spell~5~Body of C'Thun~Uncollectible": BodyofCThun,
					"Darkmoon~Neutral~Minion~6~6~6~None~Body of C'Thun~Taunt~Uncollectible": BodyofCThun_Minion,
					"Darkmoon~Neutral~Spell~5~Eye of C'Thun~Uncollectible": EyeofCThun,
					"Darkmoon~Neutral~Spell~5~Heart of C'Thun~Uncollectible": HeartofCThun,
					"Darkmoon~Neutral~Spell~5~Maw of C'Thun~Uncollectible": MawofCThun,
					"Darkmoon~Neutral~Minion~10~6~6~None~C'Thun, the Shattered~Battlecry~Start of Game~Legendary": CThuntheShattered,
					"Darkmoon~Neutral~Minion~10~1~1~Beast~Darkmoon Rabbit~Rush~Poisonous": DarkmoonRabbit,
					"Darkmoon~Neutral~Minion~10~5~7~None~N'Zoth, God of the Deep~Battlecry~Legendary": NZothGodoftheDeep,
					"Darkmoon~Neutral~Minion~10~7~5~None~Yogg-Saron, Master of Fate~Battlecry~Legendary": YoggSaronMasterofFate,
					"Darkmoon~Neutral~Minion~10~10~10~None~Y'Shaarj, the Defiler~Battlecry~Legendary": YShaarjtheDefiler,
					#Demon Hunter Cards
					"Darkmoon~Demon Hunter~Spell~1~Felscream Blast~Lifesteal": FelscreamBlast,
					"Darkmoon~Demon Hunter~Spell~1~Throw Glaive": ThrowGlaive,
					"Darkmoon~Demon Hunter~Minion~2~2~3~None~Redeemed Pariah": RedeemedPariah,
					"Darkmoon~Demon Hunter~Spell~3~Acrobatics": Acrobatics,
					"Darkmoon~Demon Hunter~Weapon~3~3~2~Dreadlord's Bite~Outcast": DreadlordsBite,
					"Darkmoon~Demon Hunter~Minion~3~4~3~Elemental~Felsteel Executioner": FelsteelExecutioner,
					"Darkmoon~Demon Hunter~Weapon~3~4~3~Felsteel Executioner~Corrupted~Uncollectible": FelsteelExecutioner_Corrupt,
					"Darkmoon~Demon Hunter~Minion~3~3~4~None~Line Hopper": LineHopper,
					"Darkmoon~Demon Hunter~Minion~3~2~5~Demon~Insatiable Felhound~Taunt": InsatiableFelhound,
					"Darkmoon~Demon Hunter~Minion~3~3~6~Demon~Insatiable Felhound~Taunt~Lifesteal~Corrupt~Uncollectible": InsatiableFelhound_Corrupt,
					"Darkmoon~Demon Hunter~Spell~3~Relentless Persuit": RelentlessPersuit,
					"Darkmoon~Demon Hunter~Minion~3~4~1~None~Stiltstepper~Battlecry": Stiltstepper,
					"Darkmoon~Demon Hunter~Minion~4~2~6~None~Il'gynoth~Lifesteal~Legendary": Ilgynoth,
					"Darkmoon~Demon Hunter~Minion~4~3~3~None~Renowned Performer~Rush~Deathrattle": RenownedPerformer,
					"Darkmoon~Demon Hunter~Minion~1~1~1~None~Performer's Assistant~Taunt~Uncollectible": PerformersAssistant,
					"Darkmoon~Demon Hunter~Minion~5~5~3~None~Zai, the Incredible~Battlecry": ZaitheIncredible,
					"Darkmoon~Demon Hunter~Minion~6~6~6~Demon~Bladed Lady~Rush": BladedLady,
					"Darkmoon~Demon Hunter~Spell~7~Expendable Performers": ExpendablePerformers,
					#Druid Cards
					"Darkmoon~Druid~Spell~2~Guess the Weight": GuesstheWeight,
					"Darkmoon~Druid~Spell~2~Lunar Eclipse": LunarEclipse,
					"Darkmoon~Druid~Spell~2~Solar Eclipse": SolarEclipse,
					"Darkmoon~Druid~Minion~3~2~2~None~Faire Arborist~Choose One": FaireArborist,
					"Darkmoon~Druid~Minion~3~2~2~None~Faire Arborist~Corrupted~Uncollectible": FaireArborist_Corrupt,
					"Darkmoon~Druid~Minion~2~2~2~None~Treant~Uncollectible": Treant_Darkmoon,
					"Darkmoon~Druid~Spell~3~Moontouched Amulet": MoontouchedAmulet,
					"Darkmoon~Druid~Spell~3~Moontouched Amulet~Corrupted~Uncollectible": MoontouchedAmulet_Corrupt,
					"Darkmoon~Druid~Minion~4~2~2~None~Kiri, Chosen of Elune~Battlecry~Legendary": KiriChosenofElune,
					"Darkmoon~Druid~Minion~5~4~6~None~Greybough~Taunt~Deathrattle~Legendary": Greybough,
					"Darkmoon~Druid~Minion~7~4~4~Beast~Umbral Owl~Rush": UmbralOwl,
					"Darkmoon~Druid~Spell~8~Cenarion Ward": CenarionWard,
					"Darkmoon~Druid~Minion~9~10~10~Elemental~Fizzy Elemental~Rush~Taunt": FizzyElemental,
					#Hunter Cards
					"Darkmoon~Hunter~Minion~1~1~1~None~Mystery Winner~Battlecry": MysteryWinner,
					"Darkmoon~Hunter~Minion~2~1~5~Beast~Dancing Cobra": DancingCobra,
					"Darkmoon~Hunter~Minion~2~1~5~Beast~Dancing Cobra~Poisonous~Corrupted~Uncollectible": DancingCobra_Corrupt,
					"Darkmoon~Hunter~Spell~2~Don't Feed the Animals": DontFeedtheAnimals,
					"Darkmoon~Hunter~Spell~2~Don't Feed the Animals~Corrupted~Uncollectible": DontFeedtheAnimals_Corrupt,
					"Darkmoon~Hunter~Spell~2~Open the Cages~~Secret": OpentheCages,
					"Darkmoon~Hunter~Spell~3~Petting Zoo": PettingZoo,
					"Darkmoon~Hunter~Minion~3~3~3~Beast~Darkmoon Strider~Uncollectible": DarkmoonStrider,
					"Darkmoon~Hunter~Weapon~4~2~2~Rinling's Rifle~Legendary": RinlingsRifle,
					"Darkmoon~Hunter~Minion~5~5~5~Beast~Trampling Rhino~Rush": TramplingRhino,
					"Darkmoon~Hunter~Minion~6~4~4~None~Maxima Blastenheimer~Battlecry~Legendary": MaximaBlastenheimer,
					"Darkmoon~Hunter~Minion~7~8~5~Mech~Darkmoon Tonk~Deathrattle": DarkmoonTonk,
					"Darkmoon~Hunter~Spell~8~Jewel of N'Zoth": JewelofNZoth,
					#Mage Cards
					"Darkmoon~Mage~Minion~2~3~2~Elemental~Confection Cyclone~Battlecry": ConfectionCyclone,
					"Darkmoon~Mage~Minion~1~1~1~Elemental~Sugar Elemental~Uncollectible": SugarElemental,
					"Darkmoon~Mage~Spell~2~Deck of Lunacy~Legendary": DeckofLunacy,
					"Darkmoon~Mage~Minion~2~2~2~None~Game Master": GameMaster,
					"Darkmoon~Mage~Spell~3~Rigged Faire Game~~Secret": RiggedFaireGame,
					"Darkmoon~Mage~Minion~4~4~4~None~Occult Conjurer~Battlecry": OccultConjurer,
					"Darkmoon~Mage~Spell~4~Ring Toss": RingToss,
					"Darkmoon~Mage~Spell~4~Ring Toss~Corrupted~Uncollectible": RingToss_Corrupted,
					"Darkmoon~Mage~Minion~5~3~5~Elemental~Firework Elemental~Battlecry": FireworkElemental,
					"Darkmoon~Mage~Minion~5~3~5~Elemental~Firework Elemental~Battlecry~Corrupted~Uncollectible": FireworkElemental,
					"Darkmoon~Mage~Minion~6~5~5~None~Sayge, Seer of Darkmoon~Battlecry~Legendary": SaygeSeerofDarkmoon,
					"Darkmoon~Mage~Spell~7~Mask of C'Thun": MaskofCThun,
					"Darkmoon~Mage~Spell~8~Grand Finale": GrandFinale,
					"Darkmoon~Mage~Minion~8~8~8~Elemental~Exploding Sparkler~Uncollectible": ExplodingSparkler,
					#Paladin Cards
					"Darkmoon~Paladin~Spell~1~Oh My Yogg!~~Secret": OhMyYogg,
					"Darkmoon~Paladin~Minion~2~2~3~Murloc~Redscale Dragontamer~Battlecry": RedscaleDragontamer,
					"Darkmoon~Paladin~Spell~2~Snack Run": SnackRun,
					"Darkmoon~Paladin~Minion~3~3~2~None~Carnival Barker": CarnivalBarker,
					"Darkmoon~Paladin~Spell~3~Day at the Faire": DayattheFaire,
					"Darkmoon~Paladin~Spell~3~Day at the Faire~Corrupted~Uncollectible": DayattheFaire_Corrupt,
					"Darkmoon~Paladin~Minion~4~3~5~None~Balloon Merchant~Battlecry": BalloonMerchant,
					"Darkmoon~Paladin~Minion~5~5~5~Mech~Carousel Gryphon~Divine Shield": CarouselGryphon,
					"Darkmoon~Paladin~Minion~5~8~8~Mech~Carousel Gryphon~Divine Shield~Taunt~Corrupted~Uncollectible": CarouselGryphon_Corrupted,
					"Darkmoon~Paladin~Minion~5~5~5~Demon~Lothraxion the Redeemed~Battlecry~Legendary": LothraxiontheRedeemed,
					"Darkmoon~Paladin~Weapon~6~3~3~Hammer of the Naaru~Battlecry": HammeroftheNaaru,
					"Darkmoon~Paladin~Minion~6~6~6~None~Holy Elemental~Taunt~Uncollectible": HolyElemental,
					"Darkmoon~Paladin~Minion~8~7~5~None~High Exarch Yrel~Battlecry~Legendary": HighExarchYrel,
					#Priest Cards
					"Darkmoon~Priest~Spell~2~Insight": Insight,
					"Darkmoon~Priest~Spell~2~Insight~Corrupted~Uncollectible": Insight_Corrupt,
					"Darkmoon~Priest~Minion~3~4~3~None~Fairground Fool~Taunt": FairgroundFool,
					"Darkmoon~Priest~Minion~3~4~7~None~Fairground Fool~Taunt~Corrupted~Uncollectible": FairgroundFool_Corrupt,
					"Darkmoon~Priest~Minion~3~2~5~None~Nazmani Bloodweaver": NazmaniBloodweaver,
					"Darkmoon~Priest~Spell~3~Palm Reading": PalmReading,
					"Darkmoon~Priest~Spell~4~Auspicious Spirits": AuspiciousSpirits,
					"Darkmoon~Priest~Spell~4~Auspicious Spirits~Corrupted~Uncollectible": AuspiciousSpirits_Corrupt,
					"Darkmoon~Priest~Minion~4~4~4~None~The Nameless One~Battlecry~Legendary": TheNamelessOne,
					"Darkmoon~Priest~Minion~5~3~3~None~Fortune Teller~Taunt~Battlecry": FortuneTeller,
					"Darkmoon~Priest~Spell~8~Idol of Y'Shaarj": IdolofYShaarj,
					"Darkmoon~Priest~Minion~8~8~8~None~G'huun the Blood God~Battlecry~Legendary": GhuuntheBloodGod,
					"Darkmoon~Priest~Minion~9~8~8~Elemental~Blood of G'huun~Taunt": BloodofGhuun,
					#Rogue Cards
					"Darkmoon~Rogue~Minion~1~2~1~Pirate~Prize Plunderer~Combo": PrizePlunderer,
					"Darkmoon~Rogue~Minion~2~3~2~None~Foxy Fraud~Battlecry": FoxyFraud,
					"Darkmoon~Rogue~Spell~2~Shadow Clone~~Secret": ShadowClone,
					"Darkmoon~Rogue~Minion~2~3~2~None~Sweet Tooth": SweetTooth,
					"Darkmoon~Priest~Minion~2~5~2~None~Sweet Tooth~Stealth~Corrupted~Uncollectible": SweetTooth_Corrupt,
					"Darkmoon~Rogue~Spell~2~Swindle": Swindle,
					"Darkmoon~Rogue~Minion~2~3~2~None~Tenwu of the Red Smoke~Battlecry~Legendary": TenwuoftheRedSmoke,
					"Darkmoon~Rogue~Spell~3~Cloak of Shadows": CloakofShadows,
					"Darkmoon~Rogue~Minion~3~4~3~None~Ticket Master~Battlecry": TicketMaster,
					"Darkmoon~Rogue~Spell~3~Tickets~Casts When Drawn~Uncollectible": Tickets,
					"Darkmoon~Rogue~Minion~3~3~3~None~Plush Bear~Uncollectible": PlushBear,
					"Darkmoon~Rogue~Spell~5~Malevolent Strike": MalevolentStrike,
					"Darkmoon~Rogue~Minion~6~5~7~None~Grand Empress Shek'zara~Battlecry~Legendary": GrandEmpressShekzara,
					#Shaman Cards
					"Darkmoon~Shaman~Spell~1~Revolve": Revolve,
					"Darkmoon~Shaman~Minion~2~2~2~Elemental~Cagematch Custodian~Battlecry": CagematchCustodian,
					"Darkmoon~Shaman~Spell~2~Deathmatch Pavilion": DeathmatchPavilion,
					"Darkmoon~Shaman~Minion~2~3~2~None~Pavilion Duelist~Uncollectible": PavilionDuelist,
					"Darkmoon~Shaman~Minion~3~0~4~Totem~Grand Totem Eys'or~Legendary": GrandTotemEysor,
					"Darkmoon~Shaman~Minion~3~3~4~Murloc~Magicfin": Magicfin,
					"Darkmoon~Shaman~Minion~3~1~2~None~Pit Master~Battlecry": PitMaster,
					"Darkmoon~Shaman~Minion~3~1~2~None~Pit Master~Battlecry~Corrupted~Uncollectible": PitMaster_Corrupt,
					"Darkmoon~Shaman~Spell~3~Stormstrike": Stormstrike,
					"Darkmoon~Shaman~Weapon~3~3~2~Whack-a-Gnoll Hammer": WhackaGnollHammer,
					"Darkmoon~Shaman~Spell~4~Dunk Tank": DunkTank,
					"Darkmoon~Shaman~Spell~4~Dunk Tank~Corrupted~Uncollectible": DunkTank_Corrupt,
					"Darkmoon~Shaman~Minion~5~4~5~None~Inara Stormcrash~Legendary": InaraStormcrash,
					#Warlock Cards
					"Darkmoon~Warlock~Spell~1~Wicked Whispers": WickedWhispers,
					"Darkmoon~Warlock~Minion~2~1~5~Demon~Midway Maniac~Taunt": MidwayManiac,
					"Darkmoon~Warlock~Spell~3~Free Admission": FreeAdmission,
					"Darkmoon~Warlock~Minion~3~3~4~Demon~Man'ari Mosher~Battlecry": ManariMosher,
					"Darkmoon~Warlock~Spell~4~Cascading Disaster": CascadingDisaster,
					"Darkmoon~Warlock~Spell~4~Cascading Disaster~Corrupted~Uncollectible": CascadingDisaster_Corrupt,
					"Darkmoon~Warlock~Spell~4~Cascading Disaster~Corrupted2~Uncollectible": CascadingDisaster_Corrupt2,
					"Darkmoon~Warlock~Minion~3~3~3~None~Revenant Pascal~Battlecry": RevenantPascal,
					"Darkmoon~Warlock~Minion~4~4~3~Demon~Fire Breather~Battlecry": FireBreather,
					"Darkmoon~Warlock~Spell~6~Deck of Chaos~Legendary": DeckofChaos,
					"Darkmoon~Warlock~Minion~6~6~4~Demon~Ring Matron~Taunt~Deathrattle": RingMatron,
					"Darkmoon~Warlock~Minion~2~3~2~Demon~Fiery Imp~Uncollectible": FieryImp,
					"Darkmoon~Warlock~Minion~6~8~8~Demon~Tickatus~Battlecry~Legendary": Tickatus,
					"Darkmoon~Warlock~Minion~6~8~8~Demon~Tickatus~Battlecry~Corrupted~Legendary~Uncollectible": Tickatus_Corrupt,
					#Warrior Cards
					"Darkmoon~Warrior~Spell~1~Stage Dive": StageDive,
					"Darkmoon~Warrior~Spell~1~Stage Dive~Corrupted~Uncollectible": StageDive_Corrupt,
					"Darkmoon~Warrior~Minion~2~1~3~Mech~Bumper Car~Rush~Deathrattle": BumperCar,
					"Darkmoon~Warrior~Minion~2~1~4~None~E.T.C., God of Metal~Legendary": ETCGodofMetal,
					"Darkmoon~Warrior~Spell~2~Minefield": Minefield,
					"Darkmoon~Warrior~Weapon~2~1~3~Ringmaster's Baton": RingmastersBaton,
					"Darkmoon~Warrior~Minion~2~3~2~Mech~Stage Hand~Battlecry": StageHand,
					"Darkmoon~Warrior~Spell~3~Feat of Strength": FeatofStrength,
					"Darkmoon~Warrior~Minion~4~2~5~Pirate~Sword Eater~Taunt~Battlecry": SwordEater,
					"Darkmoon~Warrior~Weapon~3~3~2~Jawbreaker~Uncollectible": Jawbreaker,
					"Darkmoon~Warrior~Minion~5~3~5~None~Ringmaster Whatley~Battlecry~Legendary": RingmasterWhatley,
					"Darkmoon~Warrior~Minion~5~5~5~Dragon~Tent Thrasher~Rush": TentThrasher,
					}