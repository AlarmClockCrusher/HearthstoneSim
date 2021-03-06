import math

from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import Wait, Func
from direct.showbase.ShowBase import ShowBase
from direct.task import Task

from Code2CardList import *
from Game import *
from GenerateRNGPools import *
from Panda_CustomWidgets import *

from datetime import datetime
from collections import deque

import tkinter as tk
from tkinter import messagebox

from Panda_UICommonPart import *


translateTable = {"Choose Game Board(Random by default)": "选择棋盘（默认为随机）",
				  	"Loading. Please wait":"正在加载模型，请等待",
					"Hero 1 class": "选择玩家1职业",
					"Hero 2 class": "选择玩家2职业",
					"Enter Deck 1 code": "输入玩家1的套牌代码",
					"Enter Deck 2 code": "输入玩家2的套牌代码",
					"Deck 1 incorrect": "玩家1的套牌代码有误",
					"Deck 2 incorrect": "玩家2的套牌代码有误",
					"Deck 1&2 incorrect": "玩家1与玩家2的套牌代码均有误",
					"Finished Loading. Start!": "加载完成，可以开始",
				  }

def txt(text, CHN):
	try: return translateTable[text]
	except: return text
	#if CHN:
	#	try: return translateTable[text]
	#	except: return text
	#return text

class Layer1Window:
	def __init__(self):
		self.window = tk.Tk()
		self.btn_Start = tk.Button(self.window, text=txt("Loading. Please wait", CHN), bg="red", font=("Yahei", 20, "bold"), command=self.init_ShowBase)
		
		self.gameGUI = GUI_IP(self)
		
		lbl_SelectBoard = tk.Label(master=self.window, text=txt("Choose Game Board(Random by default)", CHN), font=("Yahei", 20))
		self.boardID = tk.StringVar(self.window)
		self.boardID.set(BoardIndex[0])
		boardOpt = tk.OptionMenu(self.window, self.boardID, *BoardIndex)
		boardOpt.config(width=20, font=("Yahei", 20))
		boardOpt["menu"].config(font=("Yahei", 20))
		
		"""Create the hero class selection menu"""
		self.hero1_Var = tk.StringVar(self.window)
		self.hero1_Var.set(list(ClassDict.keys())[0])
		hero1_Opt = tk.OptionMenu(self.window, self.hero1_Var, *list(ClassDict.keys()))
		hero1_Opt.config(width=15, font=("Yahei", 20))
		hero1_Opt["menu"].config(font=("Yahei", 20))
		
		self.hero2_Var = tk.StringVar(self.window)
		self.hero2_Var.set(list(ClassDict.keys())[0])
		hero2_Opt = tk.OptionMenu(self.window, self.hero2_Var, *list(ClassDict.keys()))
		hero2_Opt.config(width=15, font=("Yahei", 20))
		hero2_Opt["menu"].config(font=("Yahei", 20))
		
		self.deck1 = tk.Entry(self.window, font=("Yahei", 13), width=30)
		self.deck2 = tk.Entry(self.window, font=("Yahei", 13), width=30)
		
		"""Place the widgets"""
		lbl_SelectBoard.grid(row=0, column=0)
		boardOpt.grid(row=1, column=0)
		self.btn_Start.grid(row=3, column=0)
		
		tk.Label(self.window, text="         ").grid(row=0, column=1)
		tk.Label(self.window, text=txt("Hero 1 class", CHN),
				 font=("Yahei", 20)).grid(row=0, column=2)
		tk.Label(self.window, text=txt("Hero 2 class", CHN),
				 font=("Yahei", 20)).grid(row=1, column=2)
		hero1_Opt.grid(row=0, column=3)
		hero2_Opt.grid(row=1, column=3)
		
		tk.Label(self.window, text=txt("Enter Deck 1 code", CHN),
				 font=("Yahei", 20)).grid(row=3, column=2)
		tk.Label(self.window, text=txt("Enter Deck 2 code", CHN),
				 font=("Yahei", 20)).grid(row=4, column=2)
		self.deck1.grid(row=3, column=3)
		self.deck2.grid(row=4, column=3)
		
		self.window.mainloop()
	
	def init_ShowBase(self):
		if self.gameGUI.loading != "Start!":
			return
		
		boardID = makeCardPool(self.boardID.get(), 0, 0)
		from CardPools import cardPool, MinionsofCost, ClassCards, NeutralCards, RNGPools
		
		hero1, hero2 = self.hero1_Var.get(), self.hero2_Var.get()
		deck1, deck2 = self.deck1.get(), self.deck2.get()
		heroes = {1: ClassDict[hero1], 2: ClassDict[hero2]}
		deckStrings = {1: deck1, 2: deck2}
		decks, decksCorrect = {1: [], 2: []}, {1: False, 2: False}
		
		for ID in range(1, 3):
			decks[ID], decksCorrect[ID], heroes[ID] = parseDeckCode(deckStrings[ID], heroes[ID], ClassDict)
		
		if decksCorrect[1] and decksCorrect[2]:
			self.gameGUI.boardID = boardID
			self.gameGUI.Game.initialize_Details(cardPool, ClassCards, NeutralCards, MinionsofCost, RNGPools, heroes[1], heroes[2], deck1=decks[1], deck2=decks[2])
			self.window.destroy()
			print("Before init mulligan display, threads are\n", threading.current_thread(), threading.enumerate())
			self.gameGUI.initMulliganDisplay()
			self.gameGUI.run()
		else:
			if not decksCorrect[1]:
				if decksCorrect[2]: messagebox.showinfo(message=txt("Deck 1 incorrect", CHN))
				else: messagebox.showinfo(message=txt("Both Deck 1&2 incorrect", CHN))
			else: messagebox.showinfo(message=txt("Deck 2 incorrect", CHN))



configVars = """
win-size 1620 900
window-title Single Player Hearthstone Simulator
clock-mode limited
clock-frame-rate 45
text-use-harfbuzz true
"""

loadPrcFileData('', configVars)


class GUI_IP(Panda_UICommon):
	def __init__(self, layer1Window):
		ShowBase.__init__(self)
		#simplepbr.init(max_lights=4)
		self.disableMouse()
		
		self.layer1Window = layer1Window
		self.UI = -2  #Starts at -2, for the mulligan stage
		self.pickablesDrawn = []
		self.board, self.btnTurnEnd = None, None
		self.mulliganStatus = {1: [0, 0, 0], 2: [0, 0, 0, 0]}
		#Attributes of the GUI
		self.selectedSubject = ""
		self.subject, self.target = None, None
		self.pos, self.choice, self.UI = -1, 0, -2  #起手调换为-2
		self.discover = None
		self.btnBeingDragged, self.arrow = None, None
		self.nodePath_CardSpecsDisplay = None
		self.intervalQueue = []
		self.intervalRunning = 0
		self.gamePlayQueue = []
		self.gamePlayThread = None
		#Flag whether the game is still loading models for the cards
		self.loading = "Loading. Please Wait"
		
		self.sansBold = self.loader.loadFont('Models\\OpenSans-Bold.ttf')
		
		self.cTrav = self.collHandler = self.raySolid = None
		self.accept("mouse1", self.mouse1_Down)
		self.accept("mouse1-up", self.mouse1_Up)
		self.accept("mouse3", self.mouse3_Down)
		self.accept("mouse3-up", self.mouse3_Up)
		
		thread_RunningAnimiations = threading.Thread(target=self.thread_AnimationManager, daemon=True)
		print("thread_RunningAnimations created", thread_RunningAnimiations)
		thread_RunningAnimiations.name = "AniManagerThread"
		thread_RunningAnimiations.start()
		self.gamePlayThread = threading.Thread(target=self.keepExecutingGamePlays, daemon=True)
		self.gamePlayThread.name = "GameThread"
		self.gamePlayThread.start()
		self.init_CollisionSetup()
		
		"""Prepare models that will be used later"""
		self.Game = Game(self)
		self.Game.mode = 0
		self.Game.Classes, self.Game.ClassesandNeutral = Classes, ClassesandNeutral
		self.Game.initialize()
		threading.Thread(target=self.preloadModel, args=(self.layer1Window.btn_Start,)).start()
	
	def preloadModel(self, btn_Start):
		#Load the models
		game = self.Game
		self.backupCardModels = {"Minion": deque([loadMinion(self, SilverHandRecruit(game, 1)) for i in range(30)]),
								 "Spell": deque([loadSpell(self, LightningBolt(game, 1)) for i in range(30)]),
								 "Weapon": deque([loadWeapon(self, FieryWarAxe(game, 1)) for i in range(30)]),
								 "Power": deque([loadPower(self, Reinforce(game, 1)) for i in range(10)]),
								 "Hero": deque([loadHero(self, LordJaraxxus(game, 1)) for i in range(30)]),
								 "Dormant": deque([loadDormant(self, BurningBladePortal(game, 1)) for i in range(2)]),
								 "MinionPlayed": deque([loadMinion_Played(self, SilverHandRecruit(game, 1)) for i in range(30)]),
								 "WeaponPlayed": deque([loadWeapon_Played(self, FieryWarAxe(game, 1)) for i in range(6)]),
								 "PowerPlayed": deque([loadPower_Played(self, Reinforce(game, 1)) for i in range(4)]),
								 "HeroPlayed": deque([loadHero_Played(self, Anduin(game, 1)) for i in range(6)]),
								 "SecretPlayed": deque([loadSecret_Played(self, FreezingTrap(game, 1)) for i in range(12)]),
								 "DormantPlayed": deque([loadDormant_Played(self, BurningBladePortal(game, 1)) for i in range(15)]),
								 "Mana": deque(), "EmptyMana": deque(), "LockedMana": deque(), "OverloadedMana": deque(),
								 "Option": deque([loadChooseOption(self, Cenarius(game, 1).options[0]) for i in range(4)]),
								 }
		self.loading = "Start!"
		btn_Start.config(text=txt("Finished Loading. Start!", CHN))
		btn_Start.config(bg="green3")
	
	def initMulliganDisplay(self):
		self.posMulligans = {1: [(8 * (i - 1), 50, -5) for i in range(len(self.Game.mulligans[1]))],
							 2: [(4 + 8 * (i - 2), 50, 5) for i in range(len(self.Game.mulligans[2]))]}
		mulliganBtns = []
		for i in range(1, 3):
			for pos, card in zip(self.posMulligans[i], self.Game.mulligans[i]):
				mulliganBtns.append(self.addinDisplayCard(card, pos, scale=0.7))
		
		btn_Mulligan = DirectButton(text=("Confirm", "Confirm", "Confirm", "Confirm"), scale=0.08,
									command=self.startMulligan)
		btn_Mulligan["extraArgs"] = [mulliganBtns, btn_Mulligan]
		btn_Mulligan.setPos(0, 0, 0)
		threading.Thread(target=self.initGameDisplay).start()
		self.taskMgr.add(self.mouseMove, "Task_MoveCard")
	
	def initGameDisplay(self):
		self.handZones = {1: HandZone(self, 1), 2: HandZone(self, 2)}
		self.boardZones = {1: BoardZone(self, 1), 2: BoardZone(self, 2)}
		self.heroZones = {1: HeroZone(self, 1), 2: HeroZone(self, 2)}
		self.deckZones = {1: DeckZone(self, 1), 2: DeckZone(self, 2)}
		self.board = Board(self)
		self.pickablesDrawn.append(self.board)
		
		self.btnTurnEnd = TurnEndButton(self)
		self.btnTurnEnd.setPos(14.4, self.board.get_y(), 1)
		self.pickablesDrawn.append(self.btnTurnEnd)
		
		heroZone = self.heroZones[self.ID if hasattr(self, "ID") else 1]
		texture = self.loader.loadTexture("Models\\BoardModels\\ManaExample.png")
		for i in range(10):
			model = self.loader.loadModel("Models\\BoardModels\\Mana.glb")
			model.reparentTo(heroZone)
			model.setPos(0, -60, 0)
			model.setTexture(model.findTextureStage('*'), texture, 1)
			self.backupCardModels["Mana"].append(model)
		texture = self.loader.loadTexture("Models\\BoardModels\\LockedMana.png")
		for i in range(10):
			model = self.loader.loadModel("Models\\BoardModels\\LockedMana.glb")
			model.reparentTo(heroZone)
			model.setPos(0, -60, 0)
			model.setTexture(model.findTextureStage('*'), texture, 1)
			self.backupCardModels["LockedMana"].append(model)
		for i in range(10):
			model = self.loader.loadModel("Models\\BoardModels\\OverloadedMana.glb")
			model.reparentTo(heroZone)
			model.setPos(0, -60, 0)
			model.setTexture(model.findTextureStage('*'), texture, 1)
			self.backupCardModels["OverloadedMana"].append(model)
		for i in range(10):
			model = self.loader.loadModel("Models\\BoardModels\\EmptyMana.glb")
			model.reparentTo(heroZone)
			model.setPos(0, -60, 0)
			self.backupCardModels["EmptyMana"].append(model)
		
		self.camLens.setFov(49.5, 27.5)
		for ID in range(1, 3):
			self.deckZones[ID].draw()
			self.handZones[ID].draw()
			self.boardZones[ID].draw()
			self.heroZones[ID].drawMana()
			self.heroZones[ID].draw()
			self.heroZones[ID].drawSecrets()
		
	def startMulligan(self, mulliganBtns, btn_Mulligan):
		self.UI = 0
		indices1 = [i for i, status in enumerate(self.mulliganStatus[1]) if status]
		indices2 = [i for i, status in enumerate(self.mulliganStatus[2]) if status]
		#self.GUI.gameBackup = self.GUI.Game.copyGame()[0]
		btn_Mulligan.destroy()
		for btn in mulliganBtns:
			self.removeBtn(btn)
		self.executeGamePlay(lambda: self.Game.Hand_Deck.mulligan(indices1, indices2))
	
	#threading.Thread(target=self.Game.Hand_Deck.mulligan, args=(indices1, indices2)).start()
	
	"""Animation control setup"""
	
	def keepExecutingGamePlays(self):
		while True:
			if self.gamePlayQueue:
				self.gamePlayQueue.pop(0)()
			time.sleep(0.02)
	
	def thread_AnimationManager(self):
		while True:
			while self.intervalQueue:
				self.intervalQueue.pop(0).start()
			time.sleep(0.02)
	
	def wrapupAnimation(self):
		self.intervalRunning -= 1
	
	#print("Finished an animation, the running flag is now", self.intervalRunning)
	
	def animate(self, animation, name="", afterAllFinished=True, blockwhilePlaying=False):
		seq = Sequence(animation, Func(self.wrapupAnimation))
		#print("Current thread is ", threading.current_thread())
		#print("All threads:", threading.enumerate())
		#print("Add the animation for '{}:'".format(name))
		if afterAllFinished:
			#print("Checking the running flag", self.intervalRunning)
			while self.intervalRunning > 0:
				time.sleep(0.02)
		#print("After waiting, the running flag is", self.intervalRunning)
		self.intervalRunning += 1
		self.intervalQueue.append(seq)
		if blockwhilePlaying:
			time.sleep(animation.getDuration())
	
	def addinDisplayCard(self, card, pos, hpr=Point3(0, 0, 0), scale=0.6, pickable=True):
		nodePath_Card = self.backupCardModels[card.type].popleft()
		nodePath_Card.changeCard(card, pickable=pickable)
		nodePath_Card.setPosHprScale(pos, hpr, Point3(scale, scale, scale))
		if pickable: self.pickablesDrawn.append(nodePath_Card)
		return nodePath_Card
	
	def removeBtn(self, btn):
		#print("Removing card and its btn", btn, btn.card)
		if btn not in self.backupCardModels[btn.card.type]:
			self.backupCardModels[btn.card.type].append(btn)
		#如果被移除的时候这个btn上面有携带卡，而且携带卡的btn就是这个btn的话，将这个btn移除
		if btn.card and btn.card.btn is btn: btn.card.btn = None
		btn.setPos(BackupModelPos)
		if btn in self.pickablesDrawn:
			self.pickablesDrawn.pop(self.pickablesDrawn.index(btn))
	
	def update(self, all=True, board=False, hand=False, hero=False, deck=False, secret=False):
		if self.UI in (0, 1, 3):
			threadName = threading.current_thread().name
			print("Update invoked by thread:", threadName)
			self.executeGamePlay(lambda: self.drawZones(all, board, hand, hero, deck, secret))
	
	def drawZones(self, all=True, board=False, hand=False, hero=False, deck=False, secret=False, blockwhilePlaying=True):
		#t1 = datetime.now()
		first, second = self.Game.turn, 3 - self.Game.turn
		if all or board:
			self.boardZones[first].draw(blockwhilePlaying=blockwhilePlaying)
			self.boardZones[second].draw(blockwhilePlaying=blockwhilePlaying)
		#t2 = datetime.now()
		#print("Drawing minionZones take: ", datetime.timestamp(t2) - datetime.timestamp(t1))
		#t1 = datetime.now()
		if all or hand:
			self.handZones[first].draw(blockwhilePlaying=blockwhilePlaying)
			self.handZones[second].draw(blockwhilePlaying=blockwhilePlaying)
		#t2 = datetime.now()
		#print("Drawing handZones take: ", datetime.timestamp(t2) - datetime.timestamp(t1))
		#t1 = datetime.now()
		if all or hero:
			self.heroZones[first].draw(blockwhilePlaying=blockwhilePlaying)
			self.heroZones[second].draw(blockwhilePlaying=blockwhilePlaying)
		#t2 = datetime.now()
		#print("Drawing heroZones take: ", datetime.timestamp(t2) - datetime.timestamp(t1))
		if all or deck:
			self.deckZones[first].draw()
			self.deckZones[second].draw()
		#t1 = datetime.now()
		if all or secret:
			self.heroZones[first].drawSecrets(blockwhilePlaying=blockwhilePlaying)
			self.heroZones[second].drawSecrets(blockwhilePlaying=blockwhilePlaying)
	
	#t2 = datetime.now()
	#print("Drawing secret zones takes: ", datetime.timestamp(t2)-datetime.timestamp(t1))
	
	def resetCardColors(self):
		for btn in self.pickablesDrawn:
			btn.setColor(white)
			if btn.card: btn.refresh(color=True, all=False)
	
	#if hasattr(btn, "nameTag_Model") and btn.nameTag_Model: btn.nameTag_Model.setColor(1, 1, 1, 1)
	#if hasattr(btn, "card_Model") and btn.card_Model: btn.card_Model.setColor()
	#if hasattr(btn, "cardImage_Model") and btn.cardImage_Model: btn.cardImage_Model.setColor(1, 1, 1, 1)
	#if hasattr(btn, "board_Model"): btn.board_Model.setColor(1, 1, 1, 1)
	
	def highlightTargets(self, legalTargets):
		for btn in self.pickablesDrawn:
			if btn.card not in legalTargets: btn.dimDown()
	
	"""Animation details"""
	
	def ensureBtnMovedAway(self, btn, nodePathType="MinionPlayed"):
		btn.setPos(BackupModelPos)
		for nodePath in self.render.findAllMatches("**/*%s*" % nodePathType):
			if nodePath.name == btn.name: nodePath.setPos(BackupModelPos)
	
	#Card/Hand animation
	def putaNewCardinHandAni(self, card):
		handZone = self.handZones[card.ID]
		print("Draw card enter hand animation")
		handZone.addaHand(card, (0, handZone.y, 0))
		handZone.draw(afterAllFinished=False)
	
	def cardReplacedinHand_Refresh(self, card):
		handZone = self.handZones[card.ID]
		ownHand = self.Game.Hand_Deck.hands[card.ID]
		#此时卡牌已经进入了玩家的手牌
		posHand = posHandsTable[handZone.z][len(ownHand)]
		hprHand = hprHandsTable[handZone.z][len(ownHand)]
		i = ownHand.index(card)
		handBtn = handZone.addaHand(card, posHand[i])
		para = Parallel(Sequence(Wait(0.2), handBtn.genMoveIntervals(pos=posHand[i], hpr=hprHand[i], duration=0.2)))
		for i, hand in enumerate(ownHand):
			if hand is not card:
				para.append(hand.btn.genMoveIntervals(pos=posHand[i], hpr=hprHand[i], duration=0.2))
		self.animate(para, blockwhilePlaying=True)
	
	#linger is for when you would like to see the card longer before it vanishes
	def cardsLeaveHandAni(self, cards, enemyCanSee=True, linger=False):
		if not isinstance(cards, (list, tuple)): cards = [cards]
		print("Draw card leaving hand animation for cards ", cards)
		handZone = self.handZones[cards[0].ID]
		para = Parallel()  #name="Parallel Cards Leave Hand")
		btns2Destroy = []
		for card in cards:
			btn = card.btn
			btns2Destroy.append(btn)
			btn.setHpr(0, 0, 0)
			para.append(btn.genMoveIntervals(pos=Point3(btn.get_x(), btn.get_y(), 0.3 * btn.get_z())))
		print("Parallel for card leaving hand", para)
		self.animate(Sequence(para, Func(handZone.removeMultiple, btns2Destroy)),
					 name="Card leaves hand ani", blockwhilePlaying=True
					 )
	
	def hand2BoardAni(self, card):
		handZone, boardZone = self.handZones[card.ID], self.boardZones[card.ID]
		btn = card.btn
		#At this point, minion has been inserted into the minions list
		ownMinions = self.Game.minions[card.ID]
		posMinions = posMinionsTable[boardZone.z][len(ownMinions)]
		pos = posMinions[ownMinions.index(card)]
		btn.setHpr(0, 0, 0)
		self.animate(Sequence(btn.genMoveIntervals(pos=Point3(pos[0], HandZone_Y - 5, 0.95 * pos[2]),
												   duration=0.25, blendType="easeOut")
							  ), blockwhilePlaying=True)
		#removeMultiple函数在调用过程中会把btn携带的牌的指向的那个button也除掉，所以不能先创造button再除掉，不然 会产生一个没有携带任何card的废button
		handZone.removeMultiple([btn])
		minionBtn = boardZone.addaMinion(card, pos=Point3(pos[0], HandZone_Y - 5 + 0.2, pos[2]))
		para = Parallel()
		for i, minion in enumerate(ownMinions):
			if minion is not card:
				para.append(minion.btn.genMoveIntervals(pos=posMinions[i], duration=0.2))
		self.animate(Sequence(para, Func(print, "mid", btn, btn.getPos(), "minion btn mid", minionBtn),
							  minionBtn.genMoveIntervals(pos=pos, duration=0.25, blendType="easeIn")))
		btn.setPos(BackupModelPos)
		#At this point, there are two btns sharing the same card, but should be fine, as the order in the pickablesDrawn guarantee that the hand card will be removed
		handZone.draw(blockwhilePlaying=False)
		print("After moving hand 2 board", btn, btn.card, btn.getPos())
	
	def deck2BoardAni(self, card):
		print("Animating deck2BoardAni")
		deckZone, boardZone = self.deckZones[card.ID], self.boardZones[card.ID]
		btn = self.addinDisplayCard(card, pos=Point3(deckZone.x, deckZone.y - 0.25, deckZone.z), hpr=(90, 0, -90), pickable=False)
		#此时随从已经 被插入minions列表
		ownMinions = self.Game.minions[card.ID]
		posMinions = posMinionsTable[boardZone.z][len(ownMinions)]
		pos = posMinions[ownMinions.index(card)]
		para = Parallel()
		para.append(Sequence(btn.genMoveIntervals(pos=Point3(deckZone.x, deckZone.y - 1.2, deckZone.z), duration=0.25),
							 btn.genMoveIntervals(pos=Point3(pos[0], pos[1] - 0.8, pos[2]))
							 )
					)
		#把召唤随从以外的随从移动，给这个随从腾出位置
		for i, minion in enumerate(ownMinions):
			if minion != card:
				para.append(minion.btn.genMoveIntervals(pos=posMinions[i], duration=0.2))
		#然后创建随从的btn，并将准备让btn开始下坠
		minionBtn = boardZone.addaMinion(card, pos=Point3(pos[0], pos[1] - 0.6, pos[2]))
		#At this point, there are two btns sharing the same card, but should be fine, as the order in the pickablesDrawn guarantee that the hand card will be removed
		seq = Sequence(para, Func(deckZone.removeMultiple, [btn]), minionBtn.genMoveIntervals(pos=pos, duration=0.25, blendType="easeIn"))
		self.animate(seq)
		deckZone.draw(blockwhilePlaying=False)
	
	#boardZone.draw(blockwhilePlaying=True)
	
	#Amulets and dormants also count as minions
	def removeMinionorWeaponAni(self, card):
		if card.type in ("Minion", "Dormant"):
			boardZone = self.boardZones[card.ID]
			#At this point, minion has left the minions list
			ownMinions = self.Game.minions[card.ID]
			posMinions = posMinionsTable[boardZone.z][len(ownMinions)]
			deadBtn = card.btn
			boardZone.removeMinion(deadBtn)
			para = Parallel()
			for i, minion in enumerate(ownMinions):
				para.append(minion.btn.genMoveIntervals(pos=posMinions[i], duration=0.2))
			self.animate(para, blockwhilePlaying=True)
			deadBtn.setPos(BackupModelPos)
		elif card.type == "Weapon":
			weaponPos = {ID: Point3(self.heroZones[ID].x - 4.5, self.heroZones[ID].y - 0.2, self.heroZones[ID].z) for ID in range(1, 3)}
			deadBtn = card.btn
			ID = card.ID
			self.heroZones[card.ID].removeWeapon(deadBtn)
			self.ensureBtnMovedAway(deadBtn, "WeaponPlayed")
			deadBtn.setPos(BackupModelPos)
		
		"""发现有时候即使这时的所有btn和nodePath检测都正确，仍然会有在update时有btn出错的情况，但nodePath好像还是正常的"""
	
	def minionAppearAni(self, card):
		print("Animating appearance of card", card)
		boardZone = self.boardZones[card.ID]
		#At this point, minion has been inserted into the minions list
		ownMinions = self.Game.minions[card.ID]
		posMinions = posMinionsTable[boardZone.z][len(ownMinions)]
		pos = posMinions[ownMinions.index(card)]
		para = Parallel()
		for i, minion in enumerate(ownMinions):
			if minion is not card:
				para.append(minion.btn.genMoveIntervals(pos=posMinions[i], duration=0.2))
		para.append(Sequence(Func(boardZone.addaMinion, card, pos), Wait(0.15)))
		self.animate(para, blockwhilePlaying=True)
	
	def board2HandAni(self, card):
		handZone, boardZone = self.handZones[card.ID], self.boardZones[card.ID]
		minionBtn = card.btn
		print("Removing minion", minionBtn)
		#At this point, minion has been inserted into the minions list
		ownMinions = self.Game.minions[card.ID]
		print("onboard minions, ", ownMinions, [minion.btn for minion in ownMinions])
		ownHand = self.Game.Hand_Deck.hands[card.ID]
		posMinions = posMinionsTable[boardZone.z][len(ownMinions)]  #此时被移回手牌的随从已经离开了minions列表
		x, y, z = minionBtn.getPos()
		para = Parallel(minionBtn.genMoveIntervals(pos=Point3(x, y - 5, z), duration=0.35))
		for i, minion in enumerate(ownMinions):
			para.append(minion.btn.genMoveIntervals(pos=posMinions[i], duration=0.35))
		self.animate(para, blockwhilePlaying=True)
		boardZone.removeMinion(minionBtn)
		handZone.addaHand(card, Point3(x, y - 5 - 0.2, z))
		self.ensureBtnMovedAway(minionBtn, nodePathType="MinionPlayed")
	
	#Only need to draw the btn, and the following addCardtoHand func handles moving the card
	
	def secretDestroyAni(self, secrets):
		self.drawZones(all=False, secret=True)
		if secrets:
			heroZone = self.heroZones[secrets[0].ID]
			pos_Start = Point3(heroZone.x, heroZone.y - 0.2, heroZone.z * 0.8)
			para = Parallel()
			left_X = -3 * (len(secrets) - 1) / 2
			btns2Destroy = []
			for i, secret in enumerate(secrets):
				btn = self.addinDisplayCard(secret, pos=pos_Start, scale=0.2, pickable=False)
				btns2Destroy.append(btn)
				para.append(btn.genMoveIntervals(pos=Point3(left_X + i * 3, 25, 0), scale=0.6, duration=0.4))
			self.animate(para, blockwhilePlaying=True)
			for btn in btns2Destroy:
				self.removeBtn(btn)
	
	def drawCardAni_1(self, card):
		print("\n\t\t---------\nDraw card by player ", card.ID, card)
		deckZone = self.deckZones[card.ID]
		pos_Pause = Point3(0.5 * deckZone.x, deckZone.y - 15, 0.2 * deckZone.z)
		handZone = self.handZones[card.ID]
		btn = handZone.addaHand(card, Point3(deckZone.x, deckZone.y - 0.25, deckZone.z), hpr=(90, 0, -90))
		
		interval = btn.genMoveIntervals(pos=pos_Pause, hpr=(0, 0, 0), duration=0.4, blendType="easeOut")
		self.animate(Sequence(interval, Wait(0.4)), name="Card leaving deck, to hand midway", blockwhilePlaying=True)
		return btn
	
	def drawCardAni_2(self, btn, newCard):
		handZone = self.handZones[btn.card.ID]
		if btn.card != newCard:
			print("Drawn card is changed")
			pos = btn.getPos()
			handZone.removeCard(btn)
			handZone.addaHand(newCard, pos)
			time.sleep(0.5)
		handZone.draw()
		print("Finish drawing card by player ", btn.card.ID, "\n\t\t---------\n")
	
	def millCardAni(self, card):
		self.drawCardAni_1(card)
	
	def fatigueAni(self, ID, damage):
		pass
	
	def cardLeavesDeckAni(self, card, enemyCanSee=True):
		pass
	
	def shuffleintoDeckAni(self, cards, enemyCanSee=True):
		ID = cards[0].ID
		deckZone = self.deckZones[ID]
		x, y, z = 0.3 * deckZone.x, deckZone.y - 15, 0.2 * deckZone.z
		para_ShuffleintoDeck, btns = Parallel(), []
		for i, card in enumerate(cards):
			btns.append(self.addinDisplayCard(card, pos=Point3(x, y + 0.2 * i, z), hpr=Point3(0, 0, 0), scale=deckScale, pickable=False))
		print("Cards to shuffle:", cards, btns)
		for btn in btns: print(btn.card, btn.getPos())
		for i, btn in enumerate(btns):
			para_ShuffleintoDeck.append(Sequence(Wait(0.4 * i + 0.6),
												 btn.genMoveIntervals(pos=Point3(deckZone.x, deckZone.y, deckZone.z), hpr=Point3(90, 0, -90)),
												 Func(lambda: self.removeBtn(btn))
												 )
										)
		self.animate(Sequence(para_ShuffleintoDeck, Func(deckZone.draw)), blockwhilePlaying=True)
	
	def showTempText(self, text):
		text = OnscreenText(text=text, pos=(0, 0), scale=0.1, fg=(1, 0, 0, 1),
							align=TextNode.ACenter, mayChange=1, font=self.sansBold,
							bg=(0.5, 0.5, 0.5, 0.8))
		Sequence(Wait(1.5), Func(text.destroy)).start()
	
	def wait(self, duration=0, showLine=False):
		pass
	
	#Attack animations
	def attackAni(self, subject, target=None):
		btn_Subject = subject.btn
		if btn_Subject in self.pickablesDrawn:
			if target:  #
				btn_Target = target.btn
				pos_Target = btn_Target.getPos()  #, Point3(0, -30 if btn_Subject.card.ID == 1 else 30, 0)
				pos_Orig, hpr_Orig = btn_Subject.getPos(), Point3(0, 0, 0)
				seq = Sequence(btn_Subject.genMoveIntervals(pos_Target, duration=0.15),
							   btn_Subject.genMoveIntervals(pos_Orig, duration=0.15),
							   btn_Subject.genMoveIntervals(Point3(btn_Subject.get_x(), btn_Subject.get_y() + 5, btn_Subject.get_z()), duration=0.1)
							   )
				self.animate(seq, blockwhilePlaying=True)
			else:  #The minion btn is lifted before it commences attack
				self.animate(Sequence(btn_Subject.genMoveIntervals(Point3(btn_Subject.get_x(), btn_Subject.get_y() - 5, btn_Subject.get_z()), duration=0.3),
									  Wait(0.05)  #Wait a bit for the following moves
									  ),
							 blockwhilePlaying=True)
	
	def cancelAttack(self, subject):
		btn = subject.btn
		if btn:
			self.animate(btn.genMoveIntervals(Point3(btn.get_x(), btn.get_y() + 5, btn.get_z()), duration=0.4))
	
	#Display card animation
	def displayCard(self, card, notSecretBeingPlayed=True):
		self.showOffBoardTrig(card)
	
	def trigBlink(self, entity, blockwhilePlaying=False, color="yellow"):
		btn = entity.btn
		if btn and hasattr(btn, "indicatorModels"):
			model = btn.indicatorModels["Trigger"]
			model.trigAni(blockwhilePlaying=blockwhilePlaying)
	
	def minionsDieAni(self, entities):
		para = Parallel()
		for entity in entities:
			btn = entity.btn
			print("Dying minion/weapon and its btn", entity, entity.btn)
			if btn:
				btn.dimDown()
				x, y, z = btn.getPos()
				dx, dz = 0.07 * np.random.rand(2)
				para.append(Sequence(btn.genMoveIntervals(pos=Point3(x + dx, y, z + dz), duration=0.1),
									 btn.genMoveIntervals(pos=Point3(x - dx, y, z - dz), duration=0.1),
									 btn.genMoveIntervals(pos=Point3(x, y, z), duration=0.1),
									 ))
		self.animate(para, blockwhilePlaying=True)
		print("Dying minion/weapons", entities, [entity.btn for entity in entities])
	
	def deathrattleAni(self, entity, color="grey40"):
		self.showOffBoardTrig(entity, animate=False)
		pos_Start = Point3(entity.x, entity.y, entity.z)
		model = self.loader.loadModel("Models\\Deathrattle.glb")
		model.setPos(pos_Start)
		model.reparentTo(self.render)
		model.setTransparency(True)
		self.animate(Sequence(LerpPosHprScaleInterval(model, duration=0.3, pos=Point3(pos_Start[0], pos_Start[1] - 1, pos_Start[2]), hpr=(0, 0, 0), scale=(2, 2, 2)),
							  model.colorInterval(duration=0.7, color=(1, 1, 1, 0))
							  )
					 )
	
	def secretTrigAni(self, secret):
		heroZone = self.heroZones[secret.ID]
		btn = secret.btn
		if btn:
			heroZone.removeCard(btn)
			heroZone.drawSecrets()
		self.showOffBoardTrig(secret)
	
	def showOffBoardTrig(self, card, alsoDisplayCard=True, notSecretBeingPlayed=True, linger=True, animate=True):
		if card:
			posEnd = Point3(-6, 25, 0)
			heroZone = self.heroZones[card.ID]
			if animate:
				nodePath_Card = self.addinDisplayCard(card, pos=Point3(heroZone.x, heroZone.y - 1, heroZone.z), scale=0.6, pickable=False)
				interval = nodePath_Card.genMoveIntervals(posEnd, duration=0.2, blendType="easeOut")
				self.animate(Sequence(interval, Wait(0.9), Func(lambda: self.removeBtn(nodePath_Card))), name="Show card ani", afterAllFinished=True)
			else:
				nodePath_Card = self.addinDisplayCard(card, pos=posEnd, scale=0.6, pickable=False)
				self.animate(Sequence(Wait(0.9), Func(lambda: self.removeBtn(nodePath_Card))), name="Show card ani", afterAllFinished=True)
	
	def eraseOffBoardTrig(self, ID):
		pass
	
	#Targeting/AOE animations
	def targetingEffectAni(self, subject, target, num, color="red"):
		btn_Subject, btn_Target = subject.btn, target.btn
		if btn_Target:
			if btn_Subject:
				x, y, z = btn_Subject.getPos()
				pos_Subject = Point3(x, y - 0.2, z)
			elif subject.type == "Minion":
				pos_Subject = Point3(subject.x, subject.y - 0.2, subject.z)
			else:
				heroZone = self.heroZones[subject.ID]
				pos_Subject = Point3(heroZone.x, heroZone.y - 0.2, heroZone.z)
			pos_Target = btn_Target.getPos()
			delta_x, delta_z = pos_Target[0] - pos_Subject[0], pos_Target[2] - pos_Subject[2]
			distance = max(0.1, math.sqrt(delta_x ** 2 + delta_z ** 2))
			angle = (180 / math.pi) * math.acos(delta_z / distance)
			if delta_x < 0: angle = -angle
			
			model = self.loader.loadModel("Models\\Fireball.glb")
			model.reparentTo(self.render)
			model.setPosHpr(pos_Subject, Point3(0, 0, angle))
			self.animate(Sequence(model.posInterval(duration=0.35, pos=pos_Target), Func(model.removeNode)), blockwhilePlaying=True)
	
	def AOEAni(self, subject, targets, numbers, color="red"):
		pass
	
	#num1: attack; num2: health or durability
	def statChangeAni(self, target, num1=None, num2=None):
		btn = target.btn
		if btn:
			threading.Thread(target=btn.refresh, kwargs={'stat': True, 'all': False}).start()  #StatBuff from aura, reset invoke this no matter what
			if num1 is not None or num2 is not None:  #Buffdebuff, heal, damage
				textNode = TextNode("StatChange Text Node")
				textNode.setAlign(TextNode.ACenter)
				textNode.setFont(self.sansBold)
				node = btn.attachNewNode(textNode)
				node.setPosHprScale(-0.1, -0.2, 0, 0, 0, 0, 1.8, 1.8, 1.8)
				if num1 is not None and num2 is not None:
					s = ""
					s += "+%d/" % num1 if num1 >= 0 else "%d/" % num1
					s += "+%d" % num2 if num2 >= 0 else "%d" % num2
					color = (0, 1, 0, 1) if num1 >= 0 or num1 >= 0 else (1, 0, 0, 1)
				elif num1 is not None:  #num2 == None
					s = "+%d" % num1 if num1 >= 0 else "%d" % num1
					color = (0, 1, 0, 1) if num1 >= 0 else (1, 0, 0, 1)
				else:  #For health change, buff is handle above, here it's only damage or heal
					s = "+%d" % num2 if num2 >= 0 else "%d" % num2
					color = (1, 1, 0, 1) if num2 >= 0 else (1, 0, 0, 1)
				textNode.setText(s)
				textNode.setTextColor(color)
				Sequence(Wait(1), Func(node.removeNode)).start()
	
	def statusChangeAni(self, card):
		btn = card.btn
		if btn:
			threading.Thread(target=btn.refresh).start()
	
	def manaChangeAni(self, card, mana_1):
		btn = card.btn
		if btn and btn.manaTextNode:
			print("ManaTextNode", btn.manaText, btn.manaTextNode)
			Sequence(btn.manaTextNode.scaleInterval(duration=0.15, scale=2 * statTextScale),
					 btn.manaTextNode.scaleInterval(duration=0.15, scale=statTextScale),
					 Func(btn.manaText.setText, str(mana_1))
					 ).start()
	
	#Miscellaneous animations
	def switchTurnAni(self):
		self.animate(self.btnTurnEnd.hprInterval(0.4, (0, 180 - self.btnTurnEnd.get_p(), 0)), name="Switch turn ani", afterAllFinished=False)
	
	def usePowerAni(self, card):
		btn = card.btn
		print("Using hero power", type(card), card, type(btn.card), btn.card)
		self.animate(btn.genMoveIntervals(hpr=Point3(180, 0, 0)), name="Use power animation", afterAllFinished=False)
	
	"""Mouse click setup"""
	
	def init_CollisionSetup(self):
		self.cTrav = CollisionTraverser()
		self.collHandler = CollisionHandlerQueue()
		
		self.raySolid = CollisionRay()
		collNode_Picker = CollisionNode("Picker Collider c_node")
		collNode_Picker.addSolid(self.raySolid)
		pickerNode = self.camera.attachNewNode(collNode_Picker)
		#pickerNode.show()  #For now, show the pickerRay collision with the card models
		self.cTrav.addCollider(pickerNode, self.collHandler)
	
	def mouse1_Down(self):
		if self.mouseWatcherNode.hasMouse():
			mpos = self.mouseWatcherNode.getMouse()
			#Reset the Collision Ray orientation, based on the mouse position
			self.raySolid.setFromLens(self.camNode, mpos.getX(), mpos.getY())
	
	def mouse1_Up(self):
		if self.mouseWatcherNode.hasMouse():
			mpos = self.mouseWatcherNode.getMouse()
			#Reset the Collision Ray orientation, based on the mouse position
			self.raySolid.setFromLens(self.camNode, mpos.getX(), mpos.getY())
			if self.collHandler.getNumEntries() > 0:
				self.collHandler.sortEntries()
				collNode_Picked = self.collHandler.getEntry(0).getIntoNodePath()
				pickedModel_NodePath = collNode_Picked.getParent()
				"""Due to unknown reasons, all node paths are involved in the render hierachy
					have their types forced into NodePath, even if they are subclasses of NodePath.
					Therefore, we have to keep a container of the subclass instance, where the original type is preserved"""
				nodePath_Picked = next((model_NodePath for model_NodePath in self.pickablesDrawn \
										if model_NodePath == pickedModel_NodePath), None)
				if nodePath_Picked:
					nodePath_Picked.leftClick()
	
	def mouse3_Down(self):
		if self.mouseWatcherNode.hasMouse():
			mpos = self.mouseWatcherNode.getMouse()
			self.raySolid.setFromLens(self.camNode, mpos.getX(), mpos.getY())
	
	def mouse3_Up(self):
		if self.mouseWatcherNode.hasMouse():
			mpos = self.mouseWatcherNode.getMouse()
			#Reset the Collision Ray orientation, based on the mouse position
			self.raySolid.setFromLens(self.camNode, mpos.getX(), mpos.getY())
			if self.collHandler.getNumEntries() > 0:
				self.collHandler.sortEntries()
				collNode_Picked = self.collHandler.getEntry(0).getIntoNodePath()
				pickedModel_NodePath = collNode_Picked.getParent()
				nodePath_Picked = next((model_NodePath for model_NodePath in self.pickablesDrawn \
										if model_NodePath == pickedModel_NodePath), None)
				if nodePath_Picked and self.UI == 0:
					nodePath_Picked.rightClick()
				else:
					self.cancelSelection()
			else:
				self.cancelSelection()
	
	def mouseMove(self, task):
		if self.mouseWatcherNode.hasMouse():
			mpos = self.mouseWatcherNode.getMouse()
			self.raySolid.setFromLens(self.camNode, mpos.getX(), mpos.getY())
			if self.arrow:
				self.removeCardSpecsDisplay()
				self.replotArrow()
			elif self.btnBeingDragged:
				self.removeCardSpecsDisplay()
				self.dragCard()
			elif self.collHandler.getNumEntries() > 0:
				self.collHandler.sortEntries()
				collNode_Picked = self.collHandler.getEntry(0).getIntoNodePath()
				picked_NodePath = collNode_Picked.getParent()
				nodePath_Picked = next((nodePath for nodePath in self.pickablesDrawn \
										if nodePath == picked_NodePath), None)
				if self.UI > -1 and nodePath_Picked:
					if nodePath_Picked.card and nodePath_Picked.card.type in ("Minion", "Spell", "Weapon", "Hero") and nodePath_Picked.card.inHand:
						if not self.nodePath_CardSpecsDisplay or self.nodePath_CardSpecsDisplay.card is not nodePath_Picked.card:
							self.drawCardSpecsDisplay(nodePath_Picked)
			elif self.nodePath_CardSpecsDisplay and hasattr(self.nodePath_CardSpecsDisplay.card, "inHand") and self.nodePath_CardSpecsDisplay.card.inHand:
				self.removeCardSpecsDisplay()
		return Task.cont
	
	def drawCardSpecsDisplay(self, btn):
		if not btn.card or (btn.card.type == "Hero" and btn.card.onBoard):
			if self.nodePath_CardSpecsDisplay: self.removeBtn(self.nodePath_CardSpecsDisplay)
			self.nodePath_CardSpecsDisplay = None
		else:  #btn是一个牌的按键
			if hasattr(btn.card, "inHand") and btn.card.inHand:
				pos = Point3(btn.get_x(), btn.get_y() - 14, 0.2 * btn.get_z())
			else:
				pos = Point3(15 if btn.get_x() >= 0 else -15, btn.get_y() - 4, 6 if btn.get_z() >= 0 else -6)
			if self.nodePath_CardSpecsDisplay:
				self.removeBtn(self.nodePath_CardSpecsDisplay)
			self.nodePath_CardSpecsDisplay = self.addinDisplayCard(btn.card, pos=pos, scale=0.8, pickable=False)
	
	def removeCardSpecsDisplay(self):
		if self.nodePath_CardSpecsDisplay:
			self.removeBtn(self.nodePath_CardSpecsDisplay)
			self.nodePath_CardSpecsDisplay = None
	
	def dragCard(self):
		if self.btnBeingDragged.collNode:
			self.btnBeingDragged.collNode.removeNode()
			self.btnBeingDragged.collNode = None
		
		#Decide the new position of the btn being dragged
		vec_X, vec_Y, vec_Z = self.raySolid.getDirection()
		y = self.btnBeingDragged.get_y()
		x, z = vec_X * y / vec_Y, vec_Z * y / vec_Y
		self.btnBeingDragged.setPosHpr(x, y, z, 0, 0, 0)
		#No need to change the x, y, z of the card being dragged(Will return anyway)
		card = self.btnBeingDragged.card
		if card.type == "Minion":
			boardZone = self.boardZones[card.ID]
			ownMinions = self.Game.minions[card.ID]
			boardSize = len(ownMinions)
			if not ownMinions:
				self.pos = -1
			else:
				temp = [minion.btn for minion in ownMinions]
				posMinions_Orig = posMinionsTable[boardZone.z][boardSize]
				posMinions_Plus1 = posMinionsTable[boardZone.z][boardSize + 1]
				if -6 > z or z > 6:  #Minion away from the center board, the minions won't shift
					posMinions = {temp[i]: posMinions_Orig[i] for i in range(boardSize)}
					self.pos = -1
				elif boardZone.z - 3.8 < z < boardZone.z + 3.8:
					#Recalculate the positions and rearrange the minion btns
					if x < temp[0].get_x():  #If placed leftmost, all current minion shift right
						posMinions = {temp[i]: posMinions_Plus1[i + 1] for i in range(boardSize)}
						self.pos = 0
					elif x < temp[-1].get_x():
						ind = next((i + 1 for i, btn in enumerate(temp[:-1]) if btn.get_x() < x < temp[i + 1].get_x()), -1)
						if ind > -1:
							posMinions = {temp[i]: posMinions_Plus1[i + (i >= ind)] for i in range(boardSize)}
							self.pos = ind
						else:
							return  #If failed to find
					else:  #All minions shift left
						posMinions = {temp[i]: posMinions_Plus1[i] for i in range(boardSize)}
						self.pos = -1
				else:  #The minion is dragged to the opponent's board, all minions shift left
					posMinions = {temp[i]: posMinions_Plus1[i] for i in range(boardSize)}
					self.pos = -1
				#para_MoveCards = Parallel()
				#for btn, pos in posMinions.items():
				#	para_MoveCards.append(btn.genMoveIntervals(pos, hpr=Point3(0, 0, 0), duration=0.05, blendType="easeOut"))
				#self.animate(para_MoveCards, name="Dragging card, move other cards", afterAllFinished=False, blockwhilePlaying=False)
				for btn, pos in posMinions.items():
					btn.setPos(pos)
	
	def stopDraggingCard(self):
		btn = self.btnBeingDragged
		if btn:
			btn.collNode = btn.attachNewNode(btn.collNode_Backup)
			ID = btn.card.ID
			#Put the card back in the right pos_hpr in hand
			handZone = self.handZones[ID]
			ownHand = self.Game.Hand_Deck.hands[ID]
			i = ownHand.index(btn.card)
			pos = posHandsTable[handZone.z][len(ownHand)][i]
			hpr = hprHandsTable[handZone.z][len(ownHand)][i]
			btn.setPosHpr(pos, hpr)
			btn.card.x, btn.card.y, btn.card.z = pos
			#Put the minions back to right positions on board
			ownMinions = self.Game.minions[ID]
			posMinions = posMinionsTable[self.boardZones[ID].z][len(ownMinions)]
			for i, minion in enumerate(ownMinions):
				minion.btn.setPos(posMinions[i])
				minion.x, minion.y, minion.z = posMinions[i]
			self.btnBeingDragged = None
	
	def replotArrow(self):
		#Decide the new orientation and scale of the arrow
		vec_X, vec_Y, vec_Z = self.raySolid.getDirection()
		btn_Subject = self.subject.btn
		x_0, y_0, z_0 = btn_Subject.getPos()
		x, z = vec_X * y_0 / vec_Y, vec_Z * y_0 / vec_Y
		delta_x, delta_z = x - x_0, z - z_0
		distance = max(0.1, math.sqrt(delta_x ** 2 + delta_z ** 2))
		angle = (180 / math.pi) * math.acos(delta_z / distance)
		if delta_x < 0: angle = -angle
		self.arrow.setScale(1, 1, distance / 7.5)
		self.arrow.setHpr(0, 0, angle)
	
	"""Game resolution setup"""
	
	def cancelSelection(self):
		self.stopDraggingCard()
		if self.arrow:
			self.arrow.removeNode()
			self.arrow = None
		if 3 > self.UI > -1:  #只有非发现状态,且游戏不在结算过程中时下才能取消选择
			if self.subject:
				for option in self.subject.options:
					if option.btn:
						print("Removing the btn of option", option, option.btn)
						self.removeBtn(option.btn)
			self.subject, self.target = None, None
			self.UI, self.pos, self.choice = 0, -1, -1
			self.selectedSubject = ""
			self.resetCardColors()
			#self.update()
			for card in self.Game.Hand_Deck.hands[1] + self.Game.Hand_Deck.hands[2] + [self.Game.powers[1]] + [self.Game.powers[2]]:
				if hasattr(card, "targets"): card.targets = []
	
	def resolveMove(self, entity, button, selectedSubject, info=None):
		game = self.Game
		if self.UI < 0:
			pass
		elif self.UI == 0:
			self.resetCardColors()
			if selectedSubject == "Board":  #Weapon won't be resolved by this functioin. It automatically cancels selection
				print("Board is not a valid subject.")
				self.cancelSelection()
			elif selectedSubject == "TurnEnds":
				self.cancelSelection()
				self.subject, self.target = None, None
				self.executeGamePlay(lambda: game.switchTurn())
				if hasattr(self, "sock"):
					print("Turn ends . Send the info to server")
					self.sendEndTurnthruServer()
			elif entity.ID != game.turn or (hasattr(self, "ID") and entity.ID != self.ID):
				print("You can only select your own characters as subject.")
				self.cancelSelection()
			else:  #选择的是我方手牌、我方英雄、我方英雄技能、我方场上随从，
				self.subject, self.target = entity, None
				self.selectedSubject = selectedSubject
				self.UI, self.choice = 2, 0  #选择了主体目标，则准备进入选择打出位置或目标界面。抉择法术可能会将界面导入抉择界面。
				button.selected = 1 - button.selected
				if self.arrow:
					self.arrow.removeNode()
					self.arrow = None
				if selectedSubject.endswith("inHand"):  #Choose card in hand as subject
					if not game.Manas.affordable(entity):  #No enough mana to use card
						self.cancelSelection()
					else:  #除了法力值不足，然后是指向性法术没有合适目标和随从没有位置使用
						typewhenPlayed = self.subject.getTypewhenPlayed()
						if typewhenPlayed == "Spell" and not entity.available():
							#法术没有可选目标，或者是不可用的非指向性法术
							self.cancelSelection()
						elif game.space(entity.ID) < 1 and (typewhenPlayed == "Minion" or typewhenPlayed == "Amulet"):  #如果场上没有空位，且目标是护符或者无法触发激奏的随从的话，则不能打出牌
							#随从没有剩余位置
							self.cancelSelection()
						else:  #Playable cards
							if entity.need2Choose():
								#所选的手牌不是影之诗卡牌，且我方有抉择全选的光环
								if not entity.index.startswith("SV_"):
									if game.status[entity.ID]["Choose Both"] > 0:
										self.choice = -1  #跳过抉择，直接进入UI=1界面。
										if entity.needTarget(-1):
											self.highlightTargets(entity.findTargets("", self.choice)[0])
									else:  #Will conduct choose one
										self.UI = 1
										for i, option in enumerate(entity.options):
											pos = (4 + 8 * (i - 1), 45, -3 if entity.ID == 1 else 3)
											self.addinDisplayCard(option, pos=pos, scale=0.8, pickable=True)
								elif entity.index.startswith("SV_"):
									self.UI = 1  #进入抉择界面，退出抉择界面的时候已经self.choice已经选好。
									return
							else:  #No need to choose one
								#如果选中的手牌是一个需要选择目标的SV法术
								if entity.index.startswith("SV_") and typewhenPlayed == "Spell" and entity.needTarget():
									self.choice = -1  #影之诗因为有抉择不发动的情况，所以不能默认choice为0（炉石中的非抉择卡牌都默认choice=0），所以需要把choice默认为-1
									#需要目标选择的影之诗卡牌开始进入多个目标的选择阶段
									game.Discover.startSelect(entity, entity.findTargets("")[0])
									return
								#选中的手牌是需要目标的炉石卡
								#可以是任何类型的炉石卡
								elif (typewhenPlayed not in ("Weapon", "Hero") and entity.needTarget()) or (typewhenPlayed == "Weapon" and entity.requireTarget):
									self.highlightTargets(entity.findTargets("", self.choice)[0])
									if typewhenPlayed != "Minion":
										print("The non-minion card you want to play requires an arrow")
										self.arrow = self.loader.loadModel("Models\\Arrow.glb")
										self.arrow.reparentTo(self.render)
										self.arrow.setPos(button.getPos())
										print("The arrow is ", self.arrow)
								self.btnBeingDragged = button
								print("Ready for drag")
				
				#不需目标的英雄技能当即使用。需要目标的进入目标选择界面。暂时不用考虑技能的抉择
				elif selectedSubject == "Power":
					print("Check if can use power", entity)
					if entity.name == "Evolve":
						self.selectedSubject = "Power"
						game.Discover.startSelect(entity, entity.findTargets("")[0])
					#英雄技能会自己判定是否可以使用。
					elif entity.needTarget():  #selectedSubject之前是"Hero Power 1"或者"Hero Power 2"
						print("Power needs target")
						self.selectedSubject = "Power"
						self.highlightTargets(entity.findTargets("", self.choice)[0])
						self.arrow = self.loader.loadModel("Models\\Arrow.glb")
						self.arrow.reparentTo(self.render)
						self.arrow.setPos(button.getPos())
					else:
						print("Request to use Hero Power {}".format(self.subject.name))
						subject = self.subject
						self.cancelSelection()
						self.subject, self.target, self.UI = subject, None, -1
						self.executeGamePlay(lambda: subject.use(None))
				#不能攻击的随从不能被选择。
				elif selectedSubject.endswith("onBoard"):
					if not entity.canAttack():
						self.cancelSelection()
					else:
						self.highlightTargets(entity.findBattleTargets()[0])
						self.arrow = self.loader.loadModel("Models\\Arrow.glb")
						self.arrow.reparentTo(self.render)
						self.arrow.setPos(button.getPos())
		elif self.UI == 1:  #在抉择界面下点击了抉择选项会进入此结算流程
			if self.arrow:
				self.arrow.removeNode()
				self.arrow = None
			if selectedSubject == "ChooseOneOption" and entity.available():
				if self.subject.index.startswith("SV_"):  #影之诗的卡牌的抉择选项确定之后进入与炉石卡不同的UI
					index = self.subject.options.index(entity)
					self.UI, self.choice = 2, index
					for option in self.subject.options:
						print("Removing the choose one option", option, option.btn)
						self.removeBtn(option.btn)
					if self.subject.needTarget(self.choice):
						self.highlightTargets(self.subject.findTargets("", self.choice)[0])
				else:  #炉石卡的抉择选项确定完毕
					#The first option is indexed as 0.
					index = self.subject.options.index(entity)
					self.UI, self.choice = 2, index
					for option in self.subject.options:
						self.removeBtn(option.btn)
					if self.subject.needTarget(self.choice) and self.subject.type == "Spell":
						self.highlightTargets(self.subject.findTargets("", self.choice)[0])
						self.arrow = self.loader.loadModel("Models\\Arrow.glb")
						self.arrow.reparentTo(self.render)
						self.arrow.setPos(button.getPos())
					else:
						self.btnBeingDragged = self.subject.btn
						print("Ready for drag")
			elif selectedSubject == "TurnEnds":
				self.cancelSelection()
				self.subject, self.target = None, None
				self.executeGamePlay(lambda: game.switchTurn())
				if hasattr(self, "sock"):
					print("Turn ends . Send the info to server")
					self.sendEndTurnthruServer()
			else:
				print("You must click an available option to continue.")
		#炉石的目标选择在此处进行
		elif self.UI == 2:  #影之诗的目标选择是不会进入这个阶段的，直接进入UI == 3，并在那里完成所有的目标选择
			self.target = entity
			print("Selected target: {}".format(entity))
			#No matter what the selections are, pressing EndTurn button ends the turn.
			#选择的主体是场上的随从或者英雄。之前的主体在UI=0的界面中已经确定一定是友方角色。
			if selectedSubject == "TurnEnds":
				self.cancelSelection()
				self.subject, self.target = None, None
				self.executeGamePlay(lambda: game.switchTurn())
				if hasattr(self, "sock"):
					print("Turn ends . Send the info to server")
					self.sendEndTurnthruServer()
			elif selectedSubject.endswith("inHand"):  #影之诗的目标选择不会在这个阶段进行
				self.cancelSelection()
			elif self.selectedSubject.endswith("onBoard"):  #已经选择了一个场上的角色，随从或英雄
				if "Hero" not in selectedSubject and selectedSubject != "MiniononBoard":
					print("Not attackable chars for minion attack, e.g. Dormant")
				else:
					print("Requesting battle: {} attacks {}".format(self.subject.name, entity))
					subject, target = self.subject, self.target
					self.cancelSelection()
					self.subject, self.target, self.UI = subject, target, -1
					self.executeGamePlay(lambda: game.battle(subject, target))
			#手中选中的随从在这里结算打出位置，如果不需要目标，则直接打出。
			#假设有时候选择随从的打出位置时会有鼠标刚好划过一个随从的情况
			elif self.selectedSubject == "MinioninHand" or self.selectedSubject == "AmuletinHand":  #选中场上的友方随从，我休眠物和护符时会把随从打出在其左侧
				if selectedSubject == "Board" or (entity.ID == self.subject.ID and (selectedSubject.endswith("onBoard") and not selectedSubject.startswith("Hero"))):
					self.selectedSubject = "MinionPosDecided"  #将主体记录为标记了打出位置的手中随从。
					#抉择随从如有全选光环，且所有选项不需目标，则直接打出。 连击随从的needTarget()由连击条件决定。
					#print("Minion {} in hand needs target: {}".format(self.subject.name, self.subject.needTarget(self.choice)))
					if not (self.subject.needTarget(self.choice) and self.subject.targetExists(self.choice)):
						#print("Requesting to play minion {} without target. The choice is {}".format(self.subject.name, self.choice))
						subject, position, choice = self.subject, self.pos, self.choice
						self.cancelSelection()
						self.subject, self.target, self.UI = subject, None, -1
						self.executeGamePlay(lambda: game.playMinion(subject, None, position, choice))
					else:  #随从打出后需要目标
						#print("The minion requires target to play. needTarget() returns {}".format(self.subject.needTarget(self.choice)))
						#需要区分SV和炉石随从的目标选择。
						subject = self.subject
						#如果是影之诗随从，则需要进入多个目标选择的UI==3阶段，而炉石随从则仍留在该阶段之路等待单目标选择的完成
						if subject.index.startswith("SV_"):  #能到这个阶段的都是有目标选择的随从
							self.choice = 0
							game.Discover.startSelect(subject, subject.findTargets("")[0])
						btn_PlayedMinion = self.subject.btn
						self.arrow = self.loader.loadModel("Models\\Arrow.glb")
						self.arrow.reparentTo(self.render)
						self.arrow.setPos(btn_PlayedMinion.getPos())
			#随从的打出位置和抉择选项已经在上一步选择，这里处理目标选择。
			elif self.selectedSubject == "MinionPosDecided":
				if selectedSubject == "MiniononBoard" or selectedSubject == "HeroonBoard":
					print("Requesting to play minion {}, targeting {} with choice: {}".format(self.subject.name, entity.name, self.choice))
					subject, position, choice = self.subject, self.pos, self.choice
					self.cancelSelection()
					self.subject, self.target, self.UI = subject, entity, -1
					self.executeGamePlay(lambda: game.playMinion(subject, entity, position, choice))
				else:
					print("Not a valid selection. All selections canceled.")
			#选中的法术已经确定抉择选项（如果有），下面决定目标选择。
			elif self.selectedSubject == "SpellinHand":
				if not self.subject.needTarget(self.choice):  #Non-targeting spells can only be cast by clicking the board
					if "Board" in selectedSubject:  #打出非指向性法术时，可以把卡牌拖动到随从，英雄或者桌面上
						print("Requesting to play spell {} without target. The choice is {}".format(self.subject.name, self.choice))
						subject, target, choice = self.subject, None, self.choice
						self.cancelSelection()
						self.subject, self.target, self.UI = subject, target, -1
						self.executeGamePlay(lambda: game.playSpell(subject, target, choice))
				else:  #法术或者法术抉择选项需要指定目标。
					if selectedSubject == "MiniononBoard" or selectedSubject == "HeroonBoard":
						print("Requesting to play spell {} with target {}. The choice is {}".format(self.subject.name, entity, self.choice))
						subject, target, choice = self.subject, entity, self.choice
						self.cancelSelection()
						self.subject, self.target, self.UI = subject, target, -1
						self.executeGamePlay(lambda: game.playSpell(subject, target, choice))
					else:
						print("Targeting spell must be cast on Hero or Minion on board.")
			#选择手牌中的武器的打出目标
			elif self.selectedSubject == "WeaponinHand":
				if not self.subject.requireTarget:
					if selectedSubject == "Board":
						print("Requesting to play Weapon {}".format(self.subject.name))
						subject, target = self.subject, None
						self.cancelSelection()
						self.subject, self.target, self.UI = subject, None, -1
						self.executeGamePlay(lambda: game.playWeapon(subject, None))
				else:
					if selectedSubject == "MiniononBoard" or selectedSubject == "HeroonBoard":
						subject, target = self.subject, entity
						print("Requesting to play weapon {} with target {}".format(subject.name, target.name))
						self.cancelSelection()
						self.subject, self.target, self.UI = subject, target, -1
						self.executeGamePlay(lambda: game.playWeapon(subject, target))
					else:
						print("Targeting weapon must be played with a target.")
			#手牌中的英雄牌是没有目标的
			elif self.selectedSubject == "HeroinHand":
				if selectedSubject == "Board":
					print("Requesting to play hero card %s" % self.subject.name)
					subject = self.subject
					self.cancelSelection()
					self.subject, self.target, self.UI = subject, None, -1
					self.executeGamePlay(lambda: game.playHero(subject))
			#Select the target for a Hero Power.
			#在此选择的一定是指向性的英雄技能。
			elif self.selectedSubject == "Power":  #如果需要指向的英雄技能对None使用，HeroPower的合法性检测会阻止使用。
				if selectedSubject == "MiniononBoard" or selectedSubject == "HeroonBoard":
					print("Requesting to use Hero Power {} on {}".format(self.subject.name, entity.name))
					subject = self.subject
					self.cancelSelection()
					self.subject, self.target, self.UI = subject, entity, -1
					self.executeGamePlay(lambda: subject.use(entity))
				else:
					print("Targeting hero power must be used with a target.")
		else:  #self.UI == 3
			if selectedSubject == "DiscoverOption":
				self.UI = 0
				self.discover = entity
			elif selectedSubject == "SelectObj":
				# print("Selecting obj for SV card")
				self.choice += 1
				self.subject.targets.append(entity)
				try:
					self.target.append(entity)
				except:
					self.target = [entity]
				if self.subject.needTarget():
					game.Discover.startSelect(self.subject, self.subject.findTargets("", self.choice)[0])
				else:  #如果目标选择完毕了，则不用再选择，直接开始打出结算
					self.UI = 0
					subject, target, position, choice = self.subject, self.subject.targets, self.pos, -1
					print("Requesting to play Shadowverse spell {} with targets {}".format(subject.name, target))
					self.cancelSelection()
					func = {"Minion": lambda: game.playMinion(subject, target, position, choice),
							"Spell": lambda: game.playSpell(subject, target, choice),
							"Amulet": lambda: game.playAmulet(subject, target, choice),
							"Power": lambda: subject.use(target, choice),
							}[subject.type]
					self.executeGamePlay(func)
			elif selectedSubject == "Fusion":
				self.UI = 0
				self.update(all=False, hand=True)
				if hasattr(self, "sock"):
					self.sendOwnMovethruServer()
				game.Discover.initiator.fusionDecided(entity)
			else:
				print("You MUST click a correct object to continue.")
	
	#Can only be invoked by the game thread
	def waitforDiscover(self, info=None):
		self.UI, self.discover = 3, None
		for i, card in enumerate(self.Game.options):
			self.addinDisplayCard(card, Point3(-5 + 5 * i, 40, 2))
		btn_HideOptions = DirectButton(text=("Hide", "Hide", "Hide", "Continue"),
									   scale=.1)
		btn_HideOptions.setPos(-10, 0, -6)
		btn_HideOptions.command = lambda: self.toggleDiscoverHide(btn_HideOptions)
		while self.discover is None:
			time.sleep(0.1)
		for card in self.Game.options:
			self.removeBtn(card.btn)
		btn_HideOptions.destroy()
		self.Game.Discover.initiator.discoverDecided(self.discover, info)
		self.discover = None
	
	def toggleDiscoverHide(self, btn):
		if btn.text == ("Hide", "Hide", "Hide", "Continue"):
			btn.text = ("Show", "Show", "Show", "Continue")
			for card in self.Game.options:
				self.removeBtn(card.btn)
		else:
			btn.text = ("Hide", "Hide", "Hide", "Continue")
			for i, card in enumerate(self.Game.options):
				self.addinDisplayCard(card, Point3(-5 + 5 * i, 40, 2))
	
	def executeGamePlay(self, func):
		self.gamePlayQueue.append(lambda: self.targetFunc4GameThread(func))
	
	#thread = threading.Thread(target=lambda: self.targetFunc4GameThread(func), daemon=True)
	#print("\n\n***********\nIn-game play thread is created", thread)
	#thread.start()
	
	def targetFunc4GameThread(self, func):
		self.UI = -1  #Lock out the selection
		for btn in self.pickablesDrawn:  #Don't show selectibility here
			btn.setBoxColor(transparent)
		func()
		self.subject, self.target, self.UI = None, None, 0
		print("After game play is finished, start updating the board")
		self.drawZones(all=False, board=True, hand=True, hero=True, deck=True, secret=True, blockwhilePlaying=False)
		print("A game play is finished\n***********\n\n")
	
	def sendOwnMovethruServer(self):
		pass
	
	def sendEndTurnthruServer(self):
		pass
	
	
	
"""Run the game"""
Layer1Window()