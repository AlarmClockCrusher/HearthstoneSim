from CardTypes import *
from Triggers_Auras import *
from numpy.random import choice as npchoice
from numpy.random import randint as nprandint
from numpy.random import shuffle as npshuffle
from numpy import inf as npinf

from Basic import TheCoin, SilverHandRecruit
from AcrossPacks import BoomBot, Lackeys

"""Awakening of Galakrond"""

"""Neutral cards"""
class SkydivingInstructor(Minion):
	Class, race, name = "Neutral", "", "Skydiving Instructor"
	mana, attack, health = 3, 2, 2
	index = "Galakrond~Neutral~Minion~3~2~2~None~Skydiving Instructor~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Summon a 1-Cost minion from your deck"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [i for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]) if card.mana == 1]
				i = npchoice(minions) if minions and curGame.space(self.ID) > 0 else -1
				curGame.fixedGuides.append(i)
			if i > -1: curGame.summonfromDeck(i, self.ID, self.pos+1, self.ID)
		return None
		
		
class Hailbringer(Minion):
	Class, race, name = "Neutral", "Elemental", "Hailbringer"
	mana, attack, health = 5, 3, 4
	index = "Galakrond~Neutral~Minion~5~3~4~Elemental~Hailbringer~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Summon two 1/1 Ice Shards that Freeze"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		pos = (self.pos, "leftandRight") if self.onBoard else (-1, "totheRightEnd")
		self.Game.summon([IceShard(self.Game, self.ID) for i in range(2)], pos, self.ID)
		return None
		
class IceShard(Minion):
	Class, race, name = "Neutral", "Elemental", "Ice Shard"
	mana, attack, health = 1, 1, 1
	index = "Galakrond~Neutral~Minion~1~1~1~Elemental~Ice Shard~Uncollectible"
	requireTarget, keyWord, description = False, "", "Freeze any character damaged by this minion"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_IceShard(self)]
		
class Trig_IceShard(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionTakesDmg", "HeroTakesDmg"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return subject == self.entity
		
	def text(self, CHN):
		return "冻结任何受到该随从伤害的角色" if CHN \
				else "Freeze any character damaged by this minion"
				
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		target.getsFrozen()
		
		
class LicensedAdventurer(Minion):
	Class, race, name = "Neutral", "", "Licensed Adventurer"
	mana, attack, health = 2, 3, 2
	index = "Galakrond~Neutral~Minion~2~3~2~None~Licensed Adventurer~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: If you control a Quest, add a Coin to your hand"
	def effCanTrig(self):
		self.effectViable = self.Game.Secrets.mainQuests[self.ID] != [] or self.Game.Secrets.sideQuests[self.ID] != []
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.Game.Secrets.mainQuests[self.ID] != [] or self.Game.Secrets.sideQuests[self.ID] != []:
			self.Game.Hand_Deck.addCardtoHand(TheCoin, self.ID, "type")
		return None
		
class FrenziedFelwing(Minion):
	Class, race, name = "Neutral", "Demon", "Frenzied Felwing"
	mana, attack, health = 4, 3, 2
	index = "Galakrond~Neutral~Minion~4~3~2~Demon~Frenzied Felwing"
	requireTarget, keyWord, description = False, "", "Costs (1) less for each damage dealt to your opponent this turn"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsHand = [Trig_FrenziedFelwing(self)]
		
	def selfManaChange(self):
		if self.inHand:
			manaReduction = self.Game.Counters.dmgonHero_inOppoTurn[3-self.ID]
			self.mana -= manaReduction
			self.mana = max(0, self.mana)
			
class Trig_FrenziedFelwing(TrigHand):
	def __init__(self, entity):
		self.blank_init(entity, ["HeroTakesDmg"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.inHand and target == self.entity.Game.heroes[3-self.entity.ID]
		
	def text(self, CHN):
		return "在本回合中，你的对手每受到1点伤害，该牌的法力值消耗便减少(1)点" if CHN \
				else "Costs (1) less for each damage dealt to your opponent this turn"
				
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Manas.calcMana_Single(self.entity)
		
		
class EscapedManasaber(Minion):
	Class, race, name = "Neutral", "Beast", "Escaped Manasaber"
	mana, attack, health = 4, 3, 5
	index = "Galakrond~Neutral~Minion~4~3~5~Beast~Escaped Manasaber~Stealth"
	requireTarget, keyWord, description = False, "Stealth", "Stealth. Whenever this attacks, gain 1 Mana Crystal this turn only"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_EscapedManasaber(self)]
		
class Trig_EscapedManasaber(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionAttackingMinion", "MinionAttackingHero"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return subject == self.entity and self.entity.onBoard
		
	def text(self, CHN):
		return "每当该随从攻击，便获得一个仅限本回合可用的法力水晶" if CHN else "Whenever this attacks, gain 1 Mana Crystal this turn only"
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		if self.entity.Game.Manas.manas[self.entity.ID] < 10:
			self.entity.Game.Manas.manas[self.entity.ID] += 1
			
			
class BoompistolBully(Minion):
	Class, race, name = "Neutral", "", "Boompistol Bully"
	mana, attack, health = 5, 5, 5
	index = "Galakrond~Neutral~Minion~5~5~5~None~Boompistol Bully~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Enemy Battlecry cards cost (5) more next turn"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		self.Game.Manas.CardAuras_Backup.append(GameManaAura_InTurnBattlecry5More(self.Game, 3-self.ID))
		return None
		
class GameManaAura_InTurnBattlecry5More(TempManaEffect):
	def __init__(self, Game, ID, changeby=0, changeto=-1):
		self.blank_init(Game, ID, +5, -1)
		self.signals = ["CardEntersHand"]
		
	def applicable(self, subject):
		return subject.ID == self.ID and "~Battlecry" in subject.index
		
		
class GrandLackeyErkh(Minion):
	Class, race, name = "Neutral", "", "Grand Lackey Erkh"
	mana, attack, health = 4, 2, 3
	index = "Galakrond~Neutral~Minion~4~2~3~None~Grand Lackey Erkh~Legendary"
	requireTarget, keyWord, description = False, "", "After you play a Lackey, add a Lackey to your hand"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_GrandLackeyErkh(self)]
		
class Trig_GrandLackeyErkh(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionBeenPlayed"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject.ID == self.entity.ID and subject.name.endswith(" Lackey")
		
	def text(self, CHN):
		return "在你使用一张跟班牌后，将一张跟班牌置入你的手牌" if CHN \
				else "After you play a Lackey, add a Lackey to your hand"
				
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			if curGame.guides:
				lackey = curGame.guides.pop(0)
			else:
				lackey = npchoice(Lackeys)
				curGame.fixedGuides.append(lackey)
			curGame.Hand_Deck.addCardtoHand(lackey, self.entity.ID, "type")
			
			
class SkyGenralKragg(Minion):
	Class, race, name = "Neutral", "Pirate", "Sky Gen'ral Kragg"
	mana, attack, health = 4, 2, 3
	index = "Galakrond~Neutral~Minion~4~2~3~Pirate~Sky Gen'ral Kragg~Taunt~Battlecry~Legendary"
	requireTarget, keyWord, description = False, "Taunt", "Taunt. Battlecry: If you've played a Quest this game, summon a 4/2 Parrot with Rush"
	def effCanTrig(self):
		self.effectViable = self.Game.Counters.hasPlayedQuestThisGame[self.ID]
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.Game.Counters.hasPlayedQuestThisGame[self.ID]:
			self.Game.summon(Sharkbait(self.Game, self.ID), self.pos+1, self.ID)
		return None
		
class Sharkbait(Minion):
	Class, race, name = "Neutral", "Beast", "Sharkbait"
	mana, attack, health = 4, 4, 2
	index = "Galakrond~Neutral~Minion~4~4~2~Beast~Sharkbait~Rush~Legendary~Uncollectible"
	requireTarget, keyWord, description = False, "Rush", "Rush"
	
	
"""Druid cards"""
class RisingWinds(Spell):
	Class, name = "Druid", "Rising Winds"
	requireTarget, mana = False, 2
	index = "Galakrond~Druid~Spell~2~Rising Winds~Twinspell~Choose One"
	description = "Twinspell. Choose One- Draw a card; or Summon a 3/2 Eagle"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.twinSpell = 1
		self.twinSpellCopy = RisingWinds2
		self.chooseOne = 1
		self.options = [TakeFlight_Option(self), SwoopIn_Option(self)]
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if choice < 1:
			self.Game.Hand_Deck.drawCard(self.ID)
		if choice != 0:
			self.Game.summon(Eagle(self.Game, self.ID), -1, self.ID)
		return None
		
class RisingWinds2(Spell):
	Class, name = "Druid", "Rising Winds"
	requireTarget, mana = False, 2
	index = "Galakrond~Druid~Spell~2~Rising Winds~Choose One~Uncollectible"
	description = "Choose One- Draw a card; or Summon a 3/2 Eagle"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.chooseOne = 1
		self.options = [TakeFlight_Option(self), SwoopIn_Option(self)]
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if choice < 1:
			self.Game.Hand_Deck.drawCard(self.ID)
		if choice != 0:
			self.Game.summon(Eagle(self.Game, self.ID), -1, self.ID)
		return None
		
class TakeFlight_Option(ChooseOneOption):
	name, description = "Take Flight", "Draw a card"
	index = "Galakrond~Druid~Spell~2~Take Flight~Uncollectible"
	
class SwoopIn_Option(ChooseOneOption):
	name, description = "Swoop In", "Summon a 3/2 Eagle"
	index = "Galakrond~Druid~Spell~2~Swoop In~Uncollectible"
	def available(self):
		return self.entity.Game.space(self.entity.ID) > 0
		
class TakeFlight(Spell):
	Class, name = "Druid", "Take Flight"
	requireTarget, mana = False, 2
	index = "Galakrond~Druid~Spell~2~Take Flight~Uncollectible"
	description = "Draw a card"
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		self.Game.Hand_Deck.drawCard(self.ID)
		return None
		
class SwoopIn(Spell):
	Class, name = "Druid", "Swoop In"
	requireTarget, mana = False, 2
	index = "Galakrond~Druid~Spell~2~Swoop In~Uncollectible"
	description = "Summon a 3/2 Eagle"
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		self.Game.summon(Eagle(self.Game, self.ID), -1, self.ID)
		return None
		
class Eagle(Minion):
	Class, race, name = "Druid", "Beast", "Eagle"
	mana, attack, health = 2, 3, 2
	index = "Galakrond~Druid~Minion~2~3~2~Beast~Eagle~Uncollectible"
	requireTarget, keyWord, description = False, "", ""
	
	
class SteelBeetle(Minion):
	Class, race, name = "Druid", "Beast", "Steel Beetle"
	mana, attack, health = 2, 2, 3
	index = "Galakrond~Druid~Minion~2~2~3~Beast~Steel Beetle~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: If you're holding a spell that costs (5) or more, gain 5 Armor"
	def effCanTrig(self):
		self.effectViable = self.Game.Hand_Deck.holdingSpellwith5CostorMore(self.ID)
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.Game.Hand_Deck.holdingSpellwith5CostorMore(self.ID):
			self.Game.heroes[self.ID].gainsArmor(5)
		return None
		
		
class WingedGuardian(Minion):
	Class, race, name = "Druid", "Beast", "Winged Guardian"
	mana, attack, health = 7, 6, 8
	index = "Galakrond~Druid~Minion~7~6~8~Beast~Winged Guardian~Taunt~Reborn"
	requireTarget, keyWord, description = False, "Taunt,Reborn", "Taunt, Reborn. Can't be targeted by spells or Hero Powers"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.marks["Evasive"] = True
		
		
"""Hunter cards"""
class FreshScent(Spell):
	Class, name = "Hunter", "Fresh Scent"
	requireTarget, mana = True, 2
	index = "Galakrond~Hunter~Spell~2~Fresh Scent~Twinspell"
	description = "Twinspell. Given a Beast +2/+2"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.twinSpell = 1
		self.twinSpellCopy = FreshScent2
		
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and "Beast" in target.race and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			target.buffDebuff(2, 2)
		return None
		
class FreshScent2(Spell):
	Class, name = "Hunter", "Fresh Scent"
	requireTarget, mana = True, 2
	index = "Galakrond~Hunter~Spell~2~Fresh Scent~Uncollectible"
	description = "Given a Beast +2/+2"
	def available(self):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and "Beast" in target.race and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			target.buffDebuff(2, 2)
		return None
		
		
class ChopshopCopter(Minion):
	Class, race, name = "Hunter", "Mech", "Chopshop Copter"
	mana, attack, health = 3, 2, 4
	index = "Galakrond~Hunter~Minion~3~2~4~Mech~Chopshop Copter"
	requireTarget, keyWord, description = False, "", "After a friendly Mech dies, add a random Mech to your hand"
	poolIdentifier = "Mechs"
	@classmethod
	def generatePool(cls, Game):
		return "Mechs", list(Game.MinionswithRace["Mech"].values())
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_ChopshopCopter(self)]
		
class Trig_ChopshopCopter(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionDied"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and target.ID == self.entity.ID and "Mech" in target.race
		
	def text(self, CHN):
		return "在一个友方机械死亡，随机将一张机械牌置入你的手牌" if CHN else "After a friendly Mech dies, add a random Mech to your hand"
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			if curGame.guides:
				mech = curGame.guides.pop(0)
			else:
				mech = npchoice(self.rngPool("Mechs"))
				curGame.fixedGuides.append(mech)
			curGame.Hand_Deck.addCardtoHand(mech, self.entity.ID, "type")
			
			
class RotnestDrake(Minion):
	Class, race, name = "Hunter", "Dragon", "Rotnest Drake"
	mana, attack, health = 5, 6, 5
	index = "Galakrond~Hunter~Minion~5~6~5~Dragon~Rotnest Drake~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: If you're holding a Dragon, destroy a random enemy minion"
	def effCanTrig(self):
		self.effectViable = self.Game.Hand_Deck.holdingDragon(self.ID, self)
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [minion.pos for minion in curGame.minionsAlive(3-self.ID)]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.minions[3-self.ID][i]
				minion.dead = True
		return None
		
		
"""Mage cards"""
class ArcaneAmplifier(Minion):
	Class, race, name = "Mage", "Elemental", "Arcane Amplifier"
	mana, attack, health = 3, 2, 5
	index = "Galakrond~Mage~Minion~3~2~5~Elemental~Arcane Amplifier"
	requireTarget, keyWord, description = False, "", "Your Hero Power deals 2 extra damage"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.auras["Your Hero Power deals 2 extra damage"] = GameRuleAura_ArcaneAmplifier(self)
		
class GameRuleAura_ArcaneAmplifier(GameRuleAura):
	def auraAppears(self):
		self.entity.Game.status[self.entity.ID]["Power Damage"] += 2
		
	def auraDisappears(self):
		self.entity.Game.status[self.entity.ID]["Power Damage"] -= 2
		
		
class AnimatedAvalanche(Minion):
	Class, race, name = "Mage", "Elemental", "Animated Avalanche"
	mana, attack, health = 7, 7, 6
	index = "Galakrond~Mage~Minion~7~7~6~Elemental~Animated Avalanche~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: If you played an Elemental last turn, summon a copy of this"
	def effCanTrig(self):
		self.effectViable = self.Game.Counters.numElementalsPlayedLastTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.Game.Counters.numElementalsPlayedLastTurn[self.ID] > 0:
			Copy = self.selfCopy(self.ID) if self.onBoard else type(self)(self.Game, self.ID)
			self.Game.summon(Copy, self.pos+1, self.ID)
		return None
		
		
class WhatDoesThisDo(HeroPower):
	mana, name, requireTarget = 0, "What Does This Do?", False
	index = "Mage~Hero Power~0~What Does This Do?"
	description = "Passive Hero Power. At the start of your turn, cast a random spell"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_WhatDoesThisDo(self)]
		
	def available(self, choice=0):
		return False
		
	def use(self, target=None, choice=0):
		return 0
		
	def appears(self):
		for trig in self.trigsBoard: trig.connect()
		self.Game.sendSignal("HeroPowerAcquired", self.ID, self, None, 0, "")
		
	def disappears(self):
		for trig in self.trigsBoard: trig.disconnect()
		
class Trig_WhatDoesThisDo(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnStarts"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return ID == self.entity.ID
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			if curGame.guides:
				spell = curGame.guides.pop(0)
			else:
				spell = npchoice(self.rngPool("Spells"))
				curGame.fixedGuides.append(spell)
			spell(curGame, self.entity.ID).cast()
			
class TheAmazingReno(Hero):
	mana, description = 10, "Battlecry: Make all minions disappear. *Poof!*"
	Class, name, heroPower, armor = "Mage", "The Amazing Reno", WhatDoesThisDo, 5
	index = "Galakrond~Mage~Hero Card~10~The Amazing Reno~Battlecry~Legendary"
	poolIdentifier = "Spells"
	@classmethod
	def generatePool(cls, Game):
		spells = []
		for Class in Game.Classes:
			spells += [value for key, value in Game.ClassCards[Class].items() if "~Spell~" in key]
		return "Spells", spells
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		for minion in self.Game.minionsonBoard(1) + self.Game.minionsonBoard(2):
			self.Game.banishMinion(self, minion)
		return None
		
		
"""Paladin cards"""
class Shotbot(Minion):
	Class, race, name = "Paladin", "Mech", "Shotbot"
	mana, attack, health = 2, 2, 2
	index = "Galakrond~Paladin~Minion~2~2~2~Mech~Shotbot~Reborn"
	requireTarget, keyWord, description = False, "Reborn", "Reborn"
	
	
class AirRaid(Spell):
	Class, name = "Paladin", "Air Raid"
	requireTarget, mana = False, 2
	index = "Galakrond~Paladin~Spell~2~Air Raid~Twinspell"
	description = "Twinspell. Summon two 1/1 Silver Hand Recruits with Taunt"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.twinSpell = 1
		self.twinSpellCopy = AirRaid2
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		minions = [SilverHandRecruit(self.Game, self.ID) for i in range(2)]
		for minion in minions: minion.keyWords["Taunt"] += 1
		self.Game.summon(minions, (-1, "totheRightEnd"), self.ID)
		return None
		
class AirRaid2(Spell):
	Class, name = "Paladin", "Air Raid"
	requireTarget, mana = False, 2
	index = "Galakrond~Paladin~Spell~2~Air Raid~Uncollectible"
	description = "Summon two 1/1 Silver Hand Recruits with Taunt"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		minions = [SilverHandRecruit(self.Game, self.ID) for i in range(2)]
		for minion in minions: minion.keyWords["Taunt"] += 1
		self.Game.summon(minions, (-1, "totheRightEnd"), self.ID)
		return None
		
		
class Scalelord(Minion):
	Class, race, name = "Paladin", "Dragon", "Scalelord"
	mana, attack, health = 5, 5, 6
	index = "Galakrond~Paladin~Minion~5~5~6~Dragon~Scalelord~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Give your Murlocs Divine Shield"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		for minion in self.Game.minionsonBoard(self.ID):
			if "Murloc" in minion.race:
				minion.getsKeyword("Divine Shield")
		return None
		
		
"""Priest cards"""
class AeonReaver(Minion):
	Class, race, name = "Priest", "Dragon", "Aeon Reaver"
	mana, attack, health = 6, 4, 4
	index = "Galakrond~Priest~Minion~6~4~4~Dragon~Aeon Reaver~Battlecry"
	requireTarget, keyWord, description = True, "", "Battlecry: Deal damage to a minion equal to its Attack"
	def targetExists(self, choice=0):
		return self.selectableMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target != self and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			self.dealsDamage(target, target.attack)
		return target
		
		
class ClericofScales(Minion):
	Class, race, name = "Priest", "", "Cleric of Scales"
	mana, attack, health = 1, 1, 1
	index = "Galakrond~Priest~Minion~1~1~1~None~Cleric of Scales~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: If you're holding a Dragon, Discover a spell from your deck"
	
	def effCanTrig(self):
		self.effectViable = self.Game.Hand_Deck.holdingDragon(self.ID)
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.Hand_Deck.holdingDragon(self.ID) and self.ID == curGame.turn:
			if curGame.mode == 0:
				if curGame.guides:
					i = curGame.guides.pop(0)
					if i > -1:
						curGame.Hand_Deck.drawCard(self.ID, i)
				else:
					spells, types = [], []
					for i, card in enumerate(curGame.Hand_Deck.decks[self.ID]):
						if card.type == "Spell" and type(card) not in types:
							spells.append(i)
							types.append(type(card))
					if spells:
						if "byOthers" in comment:
							i = npchoice(spells)
							curGame.fixedGuides.append(i)
							curGame.Hand_Deck.drawCard(self.ID, i)
						else:
							curGame.options = [curGame.Hand_Deck.decks[self.ID][i] for i in npchoice(spells, min(3, len(spells)), replace=False)]
							curGame.Discover.startDiscover(self)
					else: curGame.fixedGuides.append(-1)
		return None
		
	def discoverDecided(self, option, info):
		i = self.Game.Hand_Deck.decks[self.ID].index(option)
		self.Game.fixedGuides.append(i)
		self.Game.Hand_Deck.drawCard(self.ID, i)
		
		
class DarkProphecy(Spell):
	Class, name = "Priest", "Dark Prophecy"
	requireTarget, mana = False, 3
	index = "Galakrond~Priest~Spell~3~Dark Prophecy"
	description = "Discover a 2-Cost minion. Summon it and give it +3 Health"
	poolIdentifier = "2-Cost Minions as Priest"
	@classmethod
	def generatePool(cls, Game):
		classCards = {s : [] for s in Game.ClassesandNeutral}
		for key, value in Game.MinionsofCost[2].items():
			for Class in key.split('~')[1].split(','):
				classCards[Class].append(value)
		return ["2-Cost Minions as "+Class for Class in Game.Classes], \
			[classCards[Class]+classCards["Neutral"] for Class in Game.Classes]
			
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)(curGame, self.ID)
				minion.buffDebuff(0, 3)
				curGame.summon(minion, -1, self.ID)
			else:
				key = "2-Cost Minions as " + classforDiscover(self)
				if self.ID != curGame.turn or "byOthers" in comment:
					minion = npchoice(self.rngPool(key))
					curGame.fixedGuides.append(minion)
					minion = minion(curGame, self.ID)
					minion.buffDebuff(0, 3)
					curGame.summon(minion, -1, self.ID)
				else:
					minions = npchoice(self.rngPool(key), 3, replace=False)
					curGame.options = [minion(curGame, self.ID) for minion in minions]
					curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		option.buffDebuff(0, 3)
		self.Game.summon(option, -1, self.ID)
		
		
"""Rogue cards"""
class Skyvateer(Minion):
	Class, race, name = "Rogue", "Pirate", "Skyvateer"
	mana, attack, health = 2, 1, 3
	index = "Galakrond~Rogue~Minion~2~1~3~Pirate~Skyvateer~Stealth~Deathrattle"
	requireTarget, keyWord, description = False, "Stealth", "Stealth. Deathrattle: Draw a card"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [DrawaCard(self)]
		
class DrawaCard(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Hand_Deck.drawCard(self.entity.ID)
		
	def text(self, CHN):
		return "亡语：抽一张牌" if CHN else "Deathrattle: Draw a card"
		
		
class Waxmancy(Spell):
	Class, name = "Rogue", "Waxmancy"
	requireTarget, mana = False, 2
	index = "Galakrond~Rogue~Spell~2~Waxmancy"
	description = "Discover a Battlecry minion. Reduce its Cost by (2)"
	poolIdentifier = "Battlecry Minions as Rogue"
	@classmethod
	def generatePool(cls, Game):
		classCards = {s : [value for key, value in Game.ClassCards[s].items() if "~Minion~" in key and "~Battlecry" in key] for s in Game.Classes}
		classCards["Neutral"] = [value for key, value in Game.NeutralCards.items() if "~Minion~" in key and "~Battlecry" in key]
		return ["Battlecry Minions as "+Class for Class in Game.Classes], \
			[classCards[Class]+classCards["Neutral"] for Class in Game.Classes]
			
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)(curGame, self.ID)
				ManaMod(minion, changeby=-2, changeto=-1).applies()
				curGame.Hand_Deck.addCardtoHand(minion, self.ID, byDiscover=True)
			else:
				key = "Battlecry Minions as " + classforDiscover(self)
				if self.ID != curGame.turn or "byOthers" in comment:
					minion = npchoice(self.rngPool(key))
					curGame.fixedGuides.append(minion)
					minion = minion(curGame, self.ID)
					ManaMod(minion, changeby=-2, changeto=-1).applies()
					curGame.Hand_Deck.addCardtoHand(minion, self.ID, byDiscover=True)
				else:
					minions = npchoice(self.rngPool(key), 3, replace=False)
					curGame.options = [minion(curGame, self.ID) for minion in minions]
					curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		ManaMod(option, changeby=-2, changeto=-1).applies()
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)
		
		
class ShadowSculptor(Minion):
	Class, race, name = "Rogue", "", "Shadow Sculptor"
	mana, attack, health = 5, 3, 2
	index = "Galakrond~Rogue~Minion~5~3~2~None~Shadow Sculptor~Combo"
	requireTarget, keyWord, description = False, "", "Combo: Draw a card for each card you've played this turn"
	def effCanTrig(self):
		self.effectViable = self.Game.Counters.numCardsPlayedThisTurn[self.ID] > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if self.Game.Counters.numCardsPlayedThisTurn[self.ID] > 0:
			numCardsPlayed = self.Game.combCards(self.ID)
			for i in range(numCardsPlayed): self.Game.Hand_Deck.drawCard(self.ID)
		return None
		
"""Shaman cards"""
class ExplosiveEvolution(Spell):
	Class, name = "Shaman", "Explosive Evolution"
	requireTarget, mana = True, 2
	index = "Galakrond~Shaman~Spell~2~Explosive Evolution"
	description = "Transform a friendly minion into a random one that costs (3) more"
	poolIdentifier = "1-Cost Minions to Summon"
	@classmethod
	def generatePool(cls, Game):
		return ["%d-Cost Minions to Summon"%cost for cost in Game.MinionsofCost.keys()], \
				[list(Game.MinionsofCost[cost].values()) for cost in Game.MinionsofCost.keys()]
				
	def available(self):
		return self.selectableFriendlyMinionExists()
		
	def targetCorrect(self, target, choice=0):
		return target.type == "Minion" and target.ID == self.ID and target.onBoard
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		if target:
			curGame = self.Game
			if curGame.mode == 0:
				if curGame.guides:
					newMinion = curGame.guides.pop(0)
				else:
					cost = type(target).mana + 3
					while cost not in curGame.MinionsofCost:
						cost -= 1
					newMinion = npchoice(self.rngPool("%d-Cost Minions to Summon"%cost))
					curGame.fixedGuides.append(newMinion)
				newMinion = newMinion(curGame, target.ID)
				curGame.transform(target, newMinion)
			target = newMinion
		return target
		
		
class EyeoftheStorm(Spell):
	Class, name = "Shaman", "Eye of the Storm"
	requireTarget, mana = False, 10
	index = "Galakrond~Shaman~Spell~10~Eye of the Storm~Overload"
	description = "Summon three 5/6 Elementals with Taunt. Overload: (3)"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.overload = 3
		
	def available(self):
		return self.Game.space(self.ID) > 0
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		self.Game.summon([Stormblocker(self.Game, self.ID) for i in range(3)], (-1, "totheRightEnd"), self.ID)
		return None
		
class Stormblocker(Minion):
	Class, race, name = "Shaman", "Elemental", "Stormblocker"
	mana, attack, health = 5, 5, 6
	index = "Galakrond~Shaman~Minion~5~5~6~Elemental~Stormblocker~Taunt~Uncollectible"
	requireTarget, keyWord, description = False, "Taunt", "Taunt"
	
	
#莱登之拳对于费用不在随机池中的法术不会响应，但是埃提耶什会消耗一个耐久度，但是不会召唤随从
class TheFistofRaden(Weapon):
	Class, name, description = "Shaman", "The Fist of Ra-den", "After you cast a spell, summon a Legendary minion of that Cost. Lose 1 Durability"
	mana, attack, durability = 4, 1, 4
	index = "Galakrond~Shaman~Weapon~4~1~4~The Fist of Ra-den~Legendary"
	poolIdentifier = "1-Cost Legendary Minions to Summon"
	@classmethod
	def generatePool(cls, Game):
		minions = {}
		for key, value in Game.LegendaryMinions.items():
			s = key.split('~')[3] + "-Cost Legendary Minions to Summon"
			try: minions[s].append(value)
			except: minions[s] = [value]
		return list(minions.keys()), list(minions.values())
		
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_TheFistofRaden(self)]
		
class Trig_TheFistofRaden(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["SpellBeenPlayed"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return subject.ID == self.entity.ID and self.entity.onBoard and self.entity.durability > 0
		
	def text(self, CHN):
		return "在你施放一个法术后，召唤一个法力值消耗相同的传说随从，失去1点耐久度" if CHN \
				else "After you cast a spell, summon a Legendary minion of that Cost. Lose 1 Durability"
				
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			if curGame.guides:
				minion = curGame.guides.pop(0)
			else:
				key = "%d-Cost Legendary Minions to Summon"%number
				minion = npchoice(self.rngPool(key)) if key in curGame.RNGPools and curGame.space(self.entity.ID) > 0 else None
				curGame.fixedGuides.append(minion)
			if minion:
				curGame.summon(minion(curGame, self.entity.ID), -1, self.entity.ID)
				self.entity.loseDurability()
				
				
"""Warlock cards"""
class FiendishServant(Minion):
	Class, race, name = "Warlock", "Demon", "Fiendish Servant"
	mana, attack, health = 1, 2, 1
	index = "Galakrond~Warlock~Minion~1~2~1~Demon~Fiendish Servant~Deathrattle"
	requireTarget, keyWord, description = False, "", "Deathrattle: Give this minion's Attack to a random friendly minion"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.deathrattles = [GiveAttacktoaRandomFriendlyMinion(self)]
		
class GiveAttacktoaRandomFriendlyMinion(Deathrattle_Minion):
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		curGame = self.entity.Game
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				minions = [minion.pos for minion in curGame.minionsonBoard(self.entity.ID)]
				i = npchoice(minions) if minions else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				minion = curGame.minions[self.entity.ID][i]
				minion.buffDebuff(number, 0)
				
	def text(self, CHN):
		return "亡语：随机使一个友方随从获得该随从的攻击力" if CHN \
				else "Deathrattle: Give this minion's Attack to a random friendly minion"
				
				
class TwistedKnowledge(Spell):
	Class, name = "Warlock", "Twisted Knowledge"
	requireTarget, mana = False, 2
	index = "Galakrond~Warlock~Spell~2~Twisted Knowledge"
	description = "Discover 2 Warlock cards"
	poolIdentifier = "Warlock Cards"
	@classmethod
	def generatePool(cls, Game):
		return "Warlock", list(Game.ClassCards["Warlock"].values())
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		for num in range(2):
			curGame = self.Game
			if curGame.mode == 0:
				if curGame.guides:
					curGame.Hand_Deck.addCardtoHand(curGame.guides.pop(0), self.ID, "type", byDiscover=True)
				else:
					if self.ID != curGame.turn or "byOthers" in comment:
						card = npchoice(self.rngPool("Warlock Cards"))
						curGame.fixedGuides.append(card)
						curGame.Hand_Deck.addCardtoHand(card, self.ID, "type", byDiscover=True)
					else:
						cards = npchoice(self.rngPool("Warlock Cards"), 3, replace=False)
						curGame.options = [card(curGame, self.ID) for card in cards]
						curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)
		
#只会考虑当前的费用，寻找下回合法力值以下的牌。延时生效的法力值效果不会被考虑。
#如果被战吼触发前被对方控制了，则也会根据我方下个回合的水晶进行腐化。但是这个回合结束时就会丢弃（因为也算是一个回合。）
#https://www.bilibili.com/video/av92443139?from=search&seid=7929483619040209451
class ChaosGazer(Minion):
	Class, race, name = "Warlock", "Demon", "Chaos Gazer"
	mana, attack, health = 3, 4, 3
	index = "Galakrond~Warlock~Minion~3~4~3~Demon~Chaos Gazer~Battlecry"
	requireTarget, keyWord, description = False, "", "Battlecry: Corrupt a playable card in your opponent's hand. They have 1 turn to play it!"
	
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				i = curGame.guides.pop(0)
			else:
				manaNextTurn = max(0, min(10, curGame.Manas.manasUpper[3-self.ID] + 1) - curGame.Manas.manasOverloaded[3-self.ID])
				cards = [i for i, card in enumerate(curGame.Hand_Deck.hands[3-self.ID]) \
							if card.mana <= manaNextTurn and Trig_CorruptedHand not in [type(trig) for trig in card.trigsHand]]
				i = npchoice(cards) if cards else -1
				curGame.fixedGuides.append(i)
			if i > -1:
				card = curGame.Hand_Deck.hands[3-self.ID][i]
				trig = Trig_CorruptedHand(card)
				card.trigsHand.append(trig)
				trig.connect()
		return None
		
class Trig_CorruptedHand(TrigHand):
	def __init__(self, entity):
		self.blank_init(entity, ["TurnEnds"])
		self.inherent = False
		self.makesCardEvanescent = True
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		#被腐蚀的卡只会在其拥有者的回合结束时才会被丢弃
		return self.entity.inHand and self.entity.ID == ID
		
	def text(self, CHN):
		return "你的回合结束时，弃掉这张手牌" if CHN else "At the end of this turn, discard this card"
		
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.Hand_Deck.discardCard(self.entity.ID, self.entity)
		
		
"""Warrior cards"""
class BoomSquad(Spell):
	Class, name = "Warrior", "Boom Squad"
	requireTarget, mana = False, 1
	index = "Galakrond~Warrior~Spell~1~Boom Squad"
	description = "Discover a Lackey, Mech, or a Dragon"
	poolIdentifier = "Mechs as Warrior"
	@classmethod
	def generatePool(cls, Game):
		classes_Mech = ["Mechs as %s"+Class for Class in Game.Classes]
		classCards = {s : [] for s in Game.ClassesandNeutral}
		for key, value in Game.MinionswithRace["Mech"].items():
			for Class in key.split('~')[1].split(','):
				classCards[Class].append(value)
		mechs = [classCards[Class]+classCards["Neutral"] for Class in Game.Classes]
		classes_Dragon = ["Dragons as %s"+Class for Class in Game.Classes]
		classCards = {s : [] for s in Game.ClassesandNeutral}
		for key, value in Game.MinionswithRace["Dragon"].items():
			for Class in key.split('~')[1].split(','):
				classCards[Class].append(value)
		dragons = [classCards[Class]+classCards["Neutral"] for Class in Game.Classes]
		return classes_Mech+classes_Dragon, mechs+dragons
		
	def whenEffective(self, target=None, comment="", choice=0, posinHand=-2):
		curGame = self.Game
		if curGame.mode == 0:
			if curGame.guides:
				curGame.Hand_Deck.addCardtoHand(curGame.guides.pop(0), self.ID, "type", byDiscover=True)
			else:
				Class = classforDiscover(self)
				key_Mech, key_Dragon = "Mechs as " + Class, "Dragons as " + Class
				if self.ID != curGame.turn or "byOthers" in comment:
					mixedPool = [Lackeys, self.rngPool(key_Mech), self.rngPool(key_Dragon)]
					card = npchoice(mixedPool[nprandint(3)])
					curGame.fixedGuides.append(card)
					curGame.Hand_Deck.addCardtoHand(card, self.ID, "type", byDiscover=True)
				else:
					cards = [npchoice(Lackeys), npchoice(self.rngPool(key_Mech)), npchoice(self.rngPool(key_Dragon))]
					curGame.options = [card(curGame, self.ID) for card in cards]
					curGame.Discover.startDiscover(self)
		return None
		
	def discoverDecided(self, option, info):
		self.Game.fixedGuides.append(type(option))
		self.Game.Hand_Deck.addCardtoHand(option, self.ID, byDiscover=True)
		
		
class RiskySkipper(Minion):
	Class, race, name = "Warrior", "Pirate", "Risky Skipper"
	mana, attack, health = 1, 1, 3
	index = "Galakrond~Warrior~Minion~1~1~3~Pirate~Risky Skipper"
	requireTarget, keyWord, description = False, "", "After you play a minion, deal 1 damage to all minions"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_RiskySkipper(self)]
		
class Trig_RiskySkipper(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionBeenPlayed"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and subject.ID == self.entity.ID
		
	def text(self, CHN):
		return "在你使用一张随从牌后，对所有随从造成1点伤害" if CHN \
				else "After you play a minion, deal 1 damage to all minions"
				
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		targets = self.entity.Game.minionsonBoard(1) + self.entity.Game.minionsonBoard(2)
		self.entity.dealsAOE(targets, [1 for minion in targets])
		
	
class BombWrangler(Minion):
	Class, race, name = "Warrior", "", "Bomb Wrangler"
	mana, attack, health = 3, 2, 3
	index = "Galakrond~Warrior~Minion~3~2~3~None~Bomb Wrangler"
	requireTarget, keyWord, description = False, "", "Whenever this minion takes damage, summon a 1/1 Boom Bot"
	def __init__(self, Game, ID):
		self.blank_init(Game, ID)
		self.trigsBoard = [Trig_BombWrangler(self)]
		
class Trig_BombWrangler(TrigBoard):
	def __init__(self, entity):
		self.blank_init(entity, ["MinionTakesDmg"])
		
	def canTrig(self, signal, ID, subject, target, number, comment, choice=0):
		return self.entity.onBoard and target == self.entity
		
	def text(self, CHN):
		return "每当该随从受到伤害，召唤一个1/1的砰砰机器人" if CHN \
				else "Whenever this minion takes damage, summon a 1/1 Boom Bot"
				
	def effect(self, signal, ID, subject, target, number, comment, choice=0):
		self.entity.Game.summon(BoomBot(self.entity.Game, self.entity.ID), self.entity.pos+1, self.entity.ID)
		
				
Galakrond_Indices = {"Galakrond~Neutral~Minion~3~2~2~None~Skydiving Instructor~Battlecry": SkydivingInstructor,
					"Galakrond~Neutral~Minion~5~3~4~Elemental~Hailbringer~Battlecry": Hailbringer,
					"Galakrond~Neutral~Minion~1~1~1~Elemental~Ice Shard~Uncollectible": IceShard,
					"Galakrond~Neutral~Minion~2~3~2~None~Licensed Adventurer~Battlecry": LicensedAdventurer,
					"Galakrond~Neutral~Minion~4~3~2~Demon~Frenzied Felwing": FrenziedFelwing,
					"Galakrond~Neutral~Minion~4~3~5~Beast~Escaped Manasaber~Stealth": EscapedManasaber,
					"Galakrond~Neutral~Minion~5~5~5~None~Boompistol Bully~Battlecry": BoompistolBully,
					"Galakrond~Neutral~Minion~4~2~3~None~Grand Lackey Erkh~Legendary": GrandLackeyErkh,
					"Galakrond~Neutral~Minion~4~2~3~Pirate~Sky Gen'ral Kragg~Taunt~Battlecry~Legendary": SkyGenralKragg,
					"Galakrond~Neutral~Minion~4~4~2~Beast~Sharkbait~Rush~Legendary~Uncollectible": Sharkbait,
					"Galakrond~Druid~Spell~2~Rising Winds~Twinspell~Choose One": RisingWinds,
					"Galakrond~Druid~Spell~2~Rising Winds~Choose One~Uncollectible": RisingWinds2,
					"Galakrond~Druid~Spell~2~Take Flight~Uncollectible": TakeFlight,
					"Galakrond~Druid~Spell~2~Swoop In~Uncollectible": SwoopIn,
					"Galakrond~Druid~Minion~2~3~2~Beast~Eagle~Uncollectible": Eagle,
					"Galakrond~Druid~Minion~2~2~3~Beast~Steel Beetle~Battlecry": SteelBeetle,
					"Galakrond~Druid~Minion~7~6~8~Beast~Winged Guardian~Taunt~Reborn": WingedGuardian,
					"Galakrond~Hunter~Spell~2~Fresh Scent~Twinspell": FreshScent,
					"Galakrond~Hunter~Spell~2~Fresh Scent~Uncollectible": FreshScent2,
					"Galakrond~Hunter~Minion~3~2~4~Mech~Chopshop Copter": ChopshopCopter,
					"Galakrond~Hunter~Minion~5~6~5~Dragon~Rotnest Drake~Battlecry": RotnestDrake,
					"Galakrond~Mage~Minion~3~2~5~Elemental~Arcane Amplifier": ArcaneAmplifier,
					"Galakrond~Mage~Minion~7~7~6~Elemental~Animated Avalanche~Battlecry": AnimatedAvalanche,
					"Galakrond~Mage~Hero Card~10~The Amazing Reno~Battlecry~Legendary": TheAmazingReno,
					"Galakrond~Paladin~Minion~2~2~2~Mech~Shotbot~Reborn": Shotbot,
					"Galakrond~Paladin~Spell~2~Air Raid~Twinspell": AirRaid,
					"Galakrond~Paladin~Spell~2~Air Raid~Uncollectible": AirRaid2,
					"Galakrond~Paladin~Minion~5~5~6~Dragon~Scalelord~Battlecry": Scalelord,
					"Galakrond~Priest~Minion~6~4~4~Dragon~Aeon Reaver~Battlecry": AeonReaver,
					"Galakrond~Priest~Minion~1~1~1~None~Cleric of Scales~Battlecry": ClericofScales,
					"Galakrond~Priest~Spell~3~Dark Prophecy": DarkProphecy,
					"Galakrond~Rogue~Minion~2~1~3~Pirate~Skyvateer~Stealth~Deathrattle": Skyvateer,
					"Galakrond~Rogue~Spell~2~Waxmancy": Waxmancy,
					"Galakrond~Rogue~Minion~5~3~2~None~Shadow Sculptor~Combo": ShadowSculptor,
					"Galakrond~Shaman~Spell~2~Explosive Evolution": ExplosiveEvolution,
					"Galakrond~Shaman~Spell~10~Eye of the Storm~Overload": EyeoftheStorm,
					"Galakrond~Shaman~Minion~5~5~6~Elemental~Stormblocker~Taunt~Uncollectible": Stormblocker,
					"Galakrond~Shaman~Weapon~4~1~4~The Fist of Ra-den~Legendary": TheFistofRaden,
					"Galakrond~Warlock~Minion~1~2~1~Demon~Fiendish Servant~Deathrattle": FiendishServant,
					"Galakrond~Warlock~Spell~2~Twisted Knowledge": TwistedKnowledge,
					"Galakrond~Warlock~Minion~3~4~3~Demon~Chaos Gazer~Battlecry": ChaosGazer,
					"Galakrond~Warrior~Spell~1~Boom Squad": BoomSquad,
					"Galakrond~Warrior~Minion~1~1~3~Pirate~Risky Skipper": RiskySkipper,
					"Galakrond~Warrior~Minion~3~2~3~None~Bomb Wrangler": BombWrangler,
					}
					