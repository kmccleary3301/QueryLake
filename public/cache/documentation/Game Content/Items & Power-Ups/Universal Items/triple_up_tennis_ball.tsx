
const triple_up_tennis_ball = {
	"slug": "Triple Up Tennis Ball",
	"content": "## Overview\r\nThe \"Triple Up Tennis Ball\" is a power-up in *Top Dog*, allowing players to triple their dice roll for a turn when used.\r\n\r\n## Gameplay Interaction\r\nUtilizing the Triple Up Tennis Ball triples the dice roll value for one turn, enabling players to leap ahead on the board.\r\n\r\n## Strategy\r\nEffective use of the Triple Up Tennis Ball can be crucial for reaching **`UNKNOWN ARTICLE LINK: Board Events`** or obtaining a **[Star Ticket](/docs/game_content/items_powerups/universal_items/star_ticket)**, but players must protect it from **[Item Stealing](/docs/game_content/items_powerups/universal_items/item_stealing)**.\r\n\r\n## Balancing Considerations\r\nThe Triple Up Tennis Ball's design prevents stacking with similar items to ensure balance during gameplay.\r\n\r\n## Developer Notes\r\n- Continuous adjustment to availability and cost ensures a balanced experience.\r\n- Integration required board logic refinement to avoid unpredictable item interactions.\r\n- Usage analysis informs further balance adjustments.\r\n- A clear UI indication of its one-time use is vital to prevent confusion and frustration.\r\n\r\n## Relevant Files/Folders\r\n- \"`GAME FILE LINK: Items/Universal Items/Triple_Up_Tennis_Ball_Item.png`\": Image asset for the Triple Up Tennis Ball.\r\n- \"`GAME FILE LINK: Items/Universal Items/Triple_Up_Tennis_Ball_Item (1).png`\": Alternate image asset.\r\n\r\n## See Also\r\nAdditional information on **[[Universal Items]]** and **[[Game Modes]]** mechanics.\r\n\r\n## Cited Document Text Segments\r\n\r\n#### Source 1\r\n```text\r\nConcept Image that shows 4 players each controlling a paddle to hit the\r\nball with.\r\n\r\nPossible Idea extensions\r\n\r\nMaybe have two ball variations, a big ball that moves slower worth 2\r\npoints and a regular 1 point ball? Maybe just a variation of the regular\r\nball but it's golden (like how mario party does) and worth more points\r\n\r\nMoving platforms that can block balls to mix up play?\r\n\r\nAs far as art, we could incorporate the players moving the paddles or it\r\ncould look similar to a neon version of pong. Visuals could be simple in\r\nthat case\r\n\r\nPossible Problems\r\n```\r\n\r\n#### Source 2\r\n```text\r\n[Drop it in player's inventory as you pass them]{.mark}\r\n\r\n## [Piggy Bank]{.mark} \r\n\r\n[Starts at 0 coins, gains 2 each turn]{.mark}\r\n\r\n## [Teleporter]{.mark} \r\n\r\n[Drop receiver item and use other half to tp back]{.mark}\r\n\r\n-   [1 time use]{.mark}\r\n\r\n## [Declaration Die]{.mark} \r\n\r\n[Choose where you will go next turn. Everyone can see it]{.mark}\r\n\r\n## [Trap Square Random Warp (2 Votes)]{.mark} \r\n\r\n[Tp randomly]{.mark}\r\n\r\n## [Golden Mic:]{.mark} \r\n\r\n-   [Previously Dandy\\'s Candy]{.mark}\r\n\r\n[feed dandy\\'s and they fly you to golden bone]{.mark}\r\n\r\n## [Double Up Tennis Ball]{.mark} \r\n\r\n## [Triple Up Tennis Ball]{.mark}\r\n```\r\n\r\n#### Source 3\r\n```text\r\n## [Double Up Tennis Ball]{.mark} \r\n\r\n## [Triple Up Tennis Ball]{.mark} \r\n\r\n## [AoE Delayed Trap]{.mark} \r\n\r\n## [Affect multiple spaces and happens after X turns]{.mark}\r\n\r\n## [Lose 10 coins if in the zone]{.mark}\r\n\r\n## [Steal 5 coins from players in the zone]{.mark}\r\n\r\n## [Trap Protection]{.mark} \r\n\r\n## [Item Stealing]{.mark} \r\n\r\n-   [Trap space or 1 time use?]{.mark}\r\n\r\n## [Trap Card Trap]{.mark} \r\n\r\n-   [You buy and place it, if someone lands on it you (the trap owner)\r\n    pick what to duel for]{.mark}\r\n\r\n## [Star Ticket]{.mark} \r\n\r\n-   [If in inventory when buying a star can buy 2 stars]{.mark}\r\n```\r\n\r\n#### Source 4\r\n```text\r\nBattle Pong: Battle Pong (Name WIP)\r\n\r\nSimilar to this Pokemon Stadium game: https://youtu.be/9mz-WmzgZyo\r\n\r\nSimilar to pong, but with 4 players that are trying to score goals on\r\none another.\r\n\r\nPlayers take control of their respective \"paddles\" that can have some\r\nsort of angle/mechanic that allows them to aim where the ball goes. Once\r\na ball is hit by a player, that ball changes color and, if scored in\r\nanother player's goal, the player who hit it last receives a point.\r\n\r\nEach time a ball is hit, the speed slightly increases, so it becomes\r\nharder to keep in play.\r\n```\r\n\r\n#### Source 5\r\n```text\r\nBall needs to speed up slightly each time it is hit by a paddle\r\n\r\nBall slows down when colliding with other balls, try using Math.Clamp to\r\nlock it at its current speed as a min and a max speed so it doesn't go\r\ntoo fast.\r\n\r\nChange paddles to work with the current control system.\r\n\r\nStory Ideas\r\n\r\nGame could take place on ice, with the players as goal jockeys. Would\r\nexplain why pucks (not balls) glide so easily\r\n\r\nPucks could come in from the corners this way, would be easier to prep\r\nfor them being pitched in.\r\n```\r\n\r\n#### Source 6\r\n```text\r\nEach time a ball is hit, the speed slightly increases, so it becomes\r\nharder to keep in play.\r\n\r\nBalls spawn in slowly at first, but more can spawn in over time.\r\n\r\n1-3 maps with small variations to make the game more interesting.\r\n\r\nThings that need to be done when coming back to work on this game\r\n\r\nChange paddle shape to be angled\r\n\r\nBall needs to change color when the front of the paddle hits it, not\r\nsides or back. It also needs to change the variable lastPlayerHit to the\r\ncorrect player when it changes color.\r\n\r\nBall needs to speed up slightly each time it is hit by a paddle\r\n```\r\n\r\n#### Source 7\r\n```text\r\nWarp_Trap.png\r\n\r\nUniversal_Items.png\r\n\r\nUniversal_Items_2.png\r\n\r\nTriple_Up_Tennis_Ball_Item.png\r\n\r\nTriple_Up_Tennis_Ball_Item (1).png\r\n\r\nTrap_Repellant.png\r\n\r\nTrap_Card_Item.png\r\n\r\nTeleport V2.png\r\n\r\nSteal PickPocket Item.png\r\n\r\nReverse_Tennis_Dirty.png\r\n\r\nReverse_Tennis_Ball_Item.png\r\n\r\nReverse_Tennis_Ball_Item_V2.png\r\n\r\nReverse_Mush_Item (1).png\r\n\r\nPortal_Item.png\r\n\r\nPortal Item.png\r\n\r\nPortal Item Maybe.png\r\n\r\nPiggy_Bank_Item.png\r\n\r\nPhil\\'s_Bomb.png\r\n\r\nLavender_Sprig.png\r\n\r\nGolden_Ticket_Item.png\r\n\r\nGolden_Mic_Item.png\r\n\r\nGameGambler Item.png\r\n\r\nDouble_Up_Tennis_Ball_Item.png\r\n\r\nDelayed_Trap_Item.png\r\n\r\nDeclaration_Die.png\\'\r\n```\r\n\r\n#### Source 8\r\n```text\r\nPossible Problems\r\n\r\nI could see players doing a \"keep away\" strategy from the winning player\r\nso they can't play the game. This could get pretty frustrating. Perhaps\r\ninstead of points we could do a lives system? That way everyone gets to\r\nplay.\r\n\r\nBalls might have too linear of a trajectory. Try to think of ways to mix\r\nup their movement (balls could hit each other, map mechanics) without\r\ntaking agency away from players who want to aim their shots correctly.\r\n```\r\n\r\n#### Source 9\r\n```text\r\nShell Game:\r\n\r\n-   elimination shell game where if you pick the cup that has the ball\r\n    you get knocked out of the game it\\'s partially based on reflex,\r\n    since two players can\\'t select the same cup, so whoever picks it\r\n    first gets it\r\n\r\nCounting Game:\r\n\r\n-   Counting a number of animals/objects in a complex scene, making the\r\n    winner accuracy based\r\n\r\nSpot the Difference:\r\n\r\n-   A spot the difference game (winner is whoever finds the most\r\n    differences)\r\n\r\nBattle Pong: Battle Pong (Name WIP)\r\n\r\nSimilar to this Pokemon Stadium game: https://youtu.be/9mz-WmzgZyo\r\n```\r\n\r\n#### Source 10\r\n```text\r\nLittle Wars:\r\n\r\n-   Little Wars\r\n\r\n    -   Each player gets a variety of troops to select from then deploys\r\n        them on the battlefield.\r\n\r\n    -   Free for All\r\n\r\n    -   Here was an image showing the 4 players each placed on their own\r\n        island. Bridges connect each island over rivers. Players can\r\n        select 1 of 4 buttons to deploy a type of troop.\r\n\r\nClub Club (jousting):\r\n\r\n-   Club Club\r\n\r\n    -   Players stand on a beam (battle beam) and take part in a joust.\r\n\r\n    -   Players attempt to knock the enemy off the battle beam and into\r\n        the ball pit without hurting their teammate.\r\n```\r\n\r\n#### Source 11\r\n```text\r\nPucks could come in from the corners this way, would be easier to prep\r\nfor them being pitched in.\r\n\r\nA few ideas for this. Players could be goalies (look up equipment that\r\ngoal jockeys wear) and move back and forth to block as the paddles do.\r\nHowever, it could be more frantic and fun if players had hockey sticks\r\nand could move around the rink, spinning or hitting a button to swing\r\nthe stick to land a goal.\r\n\r\nWe could also change the games name to be something more quippy this\r\nway.\r\n\r\nConcept Image that shows 4 players each controlling a paddle to hit the\r\nball with.\r\n\r\nPossible Idea extensions\r\n```\r\n\r\n#### Source 12\r\n```text\r\n\\### Stars\r\n\r\n\\- Collect golden bones as the \\\"star\\\" equivalent\r\n\r\n\\### Mini-games\r\n\r\n\\- Shell game where players try to avoid picking cup with ball\r\n\r\n\\- Western duel/quick draw mini-game\r\n\r\n\\- Rhythm game with button prompts\r\n\r\n\\- Memory game with counting objects\r\n\r\n\\- Cooking mechanic to combine items\r\n\r\n\\- First-person shooter with silly weapons\r\n\r\n\\- Falling rock dodge game\r\n\r\n\\- Robot racing game\r\n\r\n\\- Pod racing game\r\n\r\n\\## Visuals\r\n\r\n\\### UI\r\n\r\n\\- Main menu as town square area\r\n\r\n\\- Menus styled as backstage rooms\r\n\r\n\\- Dice roll animations\r\n\r\n\\- Gashapon capsule animations\r\n\r\n\\### Characters\r\n```\r\n\r\n#### Source 13\r\n```text\r\n## Bounce Off: \r\n\r\n1)  Using the rest of a player's dice roll could prove menacing, as\r\n    someone could triple dice into moving backwards for a star. Not\r\n    terrible, but may lead to players not buying the item in favor of an\r\n    item like Break the Bank.\r\n\r\n[Keep the same]{.mark}\r\n\r\n# Enchanted Forest Items \r\n\r\n##  \r\n\r\n## Mystery Mushroom:\r\n```"
};

export default triple_up_tennis_ball;