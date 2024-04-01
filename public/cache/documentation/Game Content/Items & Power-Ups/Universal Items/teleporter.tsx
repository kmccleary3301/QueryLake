
const teleporter = {
	"slug": "Teleporter",
	"content": "## Overview\r\n\r\nThe **Teleporter** is a strategic item in Top Dog designed to quickly traverse boards.\r\n\r\n## Details\r\n\r\nThe Teleporter comes into play as a two-part item. The first part, the receiver, is placed by the player. The player can activate the second part to teleport back to the placed receiver. It is a one-time use item.\r\n\r\n## In-Game Representation\r\n\r\nIn Top Dog, the Teleporter is represented by a pair of devices.\r\n\r\n## Relevance to Gameplay\r\n\r\nThe Teleporter allows a player to control their movement, leaping across the board to a predetermined destination.\r\n\r\n## Relevant Files/Folders\r\n\r\n- Universal Items assets: \"`GAME FILE LINK: Items/Universal_Items/Teleporter.asset`\"\r\n\r\n## See Also\r\n\r\n- [[Characters]]\r\n- [[Items & Power-Ups]]\r\n- [[Game Modes]]\r\n\r\n## Developer Notes\r\n\r\n- \"The Teleporter's UX flow needs a bit more polish. Make sure the placement and activation steps are clear.\" - Dev Memo\r\n\r\n## Cited Document Text Segments\r\n\r\n#### Source 1\r\n```text\r\n> location it has teleported to. Going to Wet World may sink parts of\r\n> the map in water, which can be used to trap opponents in bad\r\n> situations. Going to Enchanted forest would put the golden acorn\r\n> mechanic into place along with the witch, etc. On top of this, item\r\n> shops (which don't change places) will sell the board specific items\r\n> of the place they have teleported to.\r\n>\r\n> I came up with this idea while making the board simulator,\r\n> specifically when I set up an enum to differentiate boards that sell\r\n> different items/event spaces do different stuff. I know it sounds\r\n```\r\n\r\n#### Source 2\r\n```text\r\nWarp_Trap.png\r\n\r\nUniversal_Items.png\r\n\r\nUniversal_Items_2.png\r\n\r\nTriple_Up_Tennis_Ball_Item.png\r\n\r\nTriple_Up_Tennis_Ball_Item (1).png\r\n\r\nTrap_Repellant.png\r\n\r\nTrap_Card_Item.png\r\n\r\nTeleport V2.png\r\n\r\nSteal PickPocket Item.png\r\n\r\nReverse_Tennis_Dirty.png\r\n\r\nReverse_Tennis_Ball_Item.png\r\n\r\nReverse_Tennis_Ball_Item_V2.png\r\n\r\nReverse_Mush_Item (1).png\r\n\r\nPortal_Item.png\r\n\r\nPortal Item.png\r\n\r\nPortal Item Maybe.png\r\n\r\nPiggy_Bank_Item.png\r\n\r\nPhil\\'s_Bomb.png\r\n\r\nLavender_Sprig.png\r\n\r\nGolden_Ticket_Item.png\r\n\r\nGolden_Mic_Item.png\r\n\r\nGameGambler Item.png\r\n\r\nDouble_Up_Tennis_Ball_Item.png\r\n\r\nDelayed_Trap_Item.png\r\n\r\nDeclaration_Die.png\\'\r\n```\r\n\r\n#### Source 3\r\n```text\r\n# Item Systems \r\n\r\n## General Questions: \r\n\r\n1)  We need to have a discussion on what items can be bought, what items\r\n    can be randomly gotten (witch vs reap and sow vs item give-away\r\n    spaces). In my simulation currently, pretty much all items can be in\r\n    shops or obtained through orb spaces at equally random rates, which\r\n    can cause some balance problems such as some players getting a 5\r\n    cost double dice while others get a 20 cost teleporter.\r\n```\r\n\r\n#### Source 4\r\n```text\r\n[Drop it in player's inventory as you pass them]{.mark}\r\n\r\n## [Piggy Bank]{.mark} \r\n\r\n[Starts at 0 coins, gains 2 each turn]{.mark}\r\n\r\n## [Teleporter]{.mark} \r\n\r\n[Drop receiver item and use other half to tp back]{.mark}\r\n\r\n-   [1 time use]{.mark}\r\n\r\n## [Declaration Die]{.mark} \r\n\r\n[Choose where you will go next turn. Everyone can see it]{.mark}\r\n\r\n## [Trap Square Random Warp (2 Votes)]{.mark} \r\n\r\n[Tp randomly]{.mark}\r\n\r\n## [Golden Mic:]{.mark} \r\n\r\n-   [Previously Dandy\\'s Candy]{.mark}\r\n\r\n[feed dandy\\'s and they fly you to golden bone]{.mark}\r\n\r\n## [Double Up Tennis Ball]{.mark} \r\n\r\n## [Triple Up Tennis Ball]{.mark}\r\n```\r\n\r\n#### Source 5\r\n```text\r\n> This map would truly encapsulate everything we want to focus on with\r\n> Top Dog: customizability. Players are dropped into a gameshow/play\r\n> stage map at first, but it will not always be that way. Players can\r\n> path towards the main focal point of the map: the host of Top-Dog.\r\n> Players can pay a fee to \"transport\" the whole map to any place in the\r\n> Top-Dog world (aka our other maps). The layout of the map stays the\r\n> same, but the map now inherits one main functional point from the map\r\n> location it has teleported to. Going to Wet World may sink parts of\r\n```"
};

export default teleporter;