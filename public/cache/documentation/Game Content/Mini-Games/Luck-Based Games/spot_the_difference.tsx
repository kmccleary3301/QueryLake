
const spot_the_difference = {
	"slug": "Spot the Difference",
	"content": "## Gameplay Overview\r\n\r\n\"Spot the Difference\" is a spot-the-difference game featured in Top Dog. Players aim to find discrepancies between two nearly identical images.\r\n\r\n## Mechanics and Rules\r\n\r\nThe winner is whoever finds the most differences between two side-by-side images.\r\n\r\n## Relevant Developer Notes\r\n\r\n- Differences between images should be subtle yet discernible.\r\n- Consider varying difficulty levels.\r\n- Images must be tested for fairness across different screen sizes and resolutions.\r\n\r\n## Relevant Files/Folders\r\n\r\n- `GAME FILE LINK: mini-games/Spot the Difference/image_set_01.png`\r\n- `GAME FILE LINK: mini-games/Spot the Difference/image_set_02.png`\r\n- `GAME FILE LINK: mini-games/Spot the Difference/image_set_03.png`\r\n\r\n![Spot the Difference Example](GAME FILE LINK: mini-games/Spot the Difference/images/sample_difference.png)\r\n\r\n## Cited Document Text Segments\r\n\r\n#### Source 1\r\n```text\r\nShell Game:\r\n\r\n-   elimination shell game where if you pick the cup that has the ball\r\n    you get knocked out of the game it\\'s partially based on reflex,\r\n    since two players can\\'t select the same cup, so whoever picks it\r\n    first gets it\r\n\r\nCounting Game:\r\n\r\n-   Counting a number of animals/objects in a complex scene, making the\r\n    winner accuracy based\r\n\r\nSpot the Difference:\r\n\r\n-   A spot the difference game (winner is whoever finds the most\r\n    differences)\r\n\r\nBattle Pong: Battle Pong (Name WIP)\r\n\r\nSimilar to this Pokemon Stadium game: https://youtu.be/9mz-WmzgZyo\r\n```\r\n\r\n#### Source 2\r\n```text\r\nMake boxes only able to be selected by one player\r\n\r\n\"As a player I would like each choice to be different\"\r\n\r\nMake box contents random\r\n\r\nHandling to make each box different\r\n\r\nWeapons\r\n\r\n\"As a player I want my random weapon to be different each turn\"\r\n\r\nCreate weapon prefabs with various stats/\"ratings\"\r\n\r\nCreate animations for weapons and firing\r\n\r\n\"As a player I would like to deal damage to my enemy\"\r\n\r\nCreate health bars for each player\r\n\r\nMake weapons damage player health if the rating is higher than the other\r\nplayer's weapon\r\n\r\nEnd Game\r\n\r\n\"As a player I would like win if my opponent's health reaches 0\"\r\n```\r\n\r\n#### Source 3\r\n```text\r\nEach weapon has a \"rating\". Higher rated weapons beat lower rated\r\nweapons and the difference in the rating is dealt as damage to the\r\nloser. Game continues in this manner until one player loses all of their\r\nstarting health.\r\n\r\nAsk at meeting what to do before game starts ex: tutorial, countdown,\r\nanimation\r\n\r\nRandom Boxes\r\n\r\n\"As a player I would like to click on a random box\"\r\n\r\nMake boxes Selectable\r\n\r\nMake box contents hidden\r\n\r\n\"As a player I would like to pick a different box from my opponent\"\r\n\r\nMake boxes only able to be selected by one player\r\n\r\n\"As a player I would like each choice to be different\"\r\n```\r\n\r\n#### Source 4\r\n```text\r\n> The main function of the map is the clock hands, both of which can be\r\n> controlled by the player at specific spots (undecided where, but\r\n> likely at spots outside the outer ring so they aren't used that\r\n> frequently) on the map. Note that the clock is broken, so the hands do\r\n> not move by themselves and have to be manually moved. Players who pay\r\n> to change the hands will set a time (within certain balancing limits,\r\n> maybe only moves forward or back by 15-30 minutes, 3-6 hours on\r\n> different hands), and the hands will move to that position, either 1)\r\n```\r\n\r\n#### Source 5\r\n```text\r\n> different items/event spaces do different stuff. I know it sounds\r\n> hard, but if we made the map super generic it could work. If every\r\n> board had a different event space action, for example, every time the\r\n> board switches, we just switch the event space to do what it would\r\n> have done on the board that was switched to.\r\n```\r\n\r\n#### Source 6\r\n```text\r\nprovide us with the story of why the characters are going on an\r\n        adventure to all of these different parts of their world to\r\n        collect these golden bones, maybe they have to pay off their\r\n        debt to Phil with golden bones? It could provide for a really\r\n        cool single player mode later down the line, and even greater,\r\n        Phil minigames could be based on different casino games, which\r\n        are \"always rigged in favor of the house.\" If we think that this\r\n        is a cool direction for the game, I can try writing up a story\r\n```\r\n\r\n#### Source 7\r\n```text\r\n> location it has teleported to. Going to Wet World may sink parts of\r\n> the map in water, which can be used to trap opponents in bad\r\n> situations. Going to Enchanted forest would put the golden acorn\r\n> mechanic into place along with the witch, etc. On top of this, item\r\n> shops (which don't change places) will sell the board specific items\r\n> of the place they have teleported to.\r\n>\r\n> I came up with this idea while making the board simulator,\r\n> specifically when I set up an enum to differentiate boards that sell\r\n> different items/event spaces do different stuff. I know it sounds\r\n```\r\n\r\n#### Source 8\r\n```text\r\n> different hands), and the hands will move to that position, either 1)\r\n> pushing players to the spot where the hand stops or 2) just hurting\r\n> them and taking coins. This acts to change how to get to the middle of\r\n> the stage, which is the best place to get around the clock quickly.\r\n>\r\n> An interesting mechanic could be helping the inhabitants of the garage\r\n> fix the clock by setting the clock to the exact right time, thus\r\n> creating another win condition for the player. Hints could be\r\n> scattered around the map in notebooks, with notes on what time the\r\n```\r\n\r\n#### Source 9\r\n```text\r\n### Art \r\n\r\nThe following are some art assets for the Top Dog game:\r\n\r\n\"ClubClubDog.png\" Some initial still image of Doug\r\n\r\n\"ClubClubDogLineup.png\" Doug in various different color variations\r\n\r\n\"DougModelLineupHD.png\" Different angles of the Doug model\r\n\r\n\"LeftHands.png\" Images of Doug's left hand. Some are seen in normal\r\npositions but others have a gun held in them\r\n\r\n\"ClubClubDogAlt1.png\" An alternate color scheme for Doug shown in the\r\nModel Lineup png\r\n\r\n\"ClubClubDogAlt2.png\" An alternate color scheme for Doug shown in the\r\nModel Lineup png\r\n```\r\n\r\n#### Source 10\r\n```text\r\n##### Minigame Time Estimates: \r\n\r\n-   Blocking out/Testing -\r\n\r\n-   Art Pass 1/Testing -\r\n\r\n-   Art Pass 2/Testing -\r\n\r\n-   Quality Assurance -\r\n\r\n-   Art Pass 3/Testing -\r\n\r\n-   Finalization -\r\n\r\nTo Daniel: Minigames are a different beast than maps so feel free to\r\nre-draft the steps required for art passes if you'd like, adding less or\r\nmore.\r\n\r\n#### Character Assets \r\n\r\n-   10 Characters\r\n\r\n    -   Palette Swap Alternates\r\n\r\n    -   More Complex alternates (if we do some kind of skin/battle pass\r\n        idea)\r\n\r\n-   Animations for all characters\r\n\r\n##### Character Time Estimates: \r\n\r\n#### Shaders\r\n```\r\n\r\n#### Source 11\r\n```text\r\n# Easy Stages: \r\n\r\n# Medium Stages: \r\n\r\n## Phil's Grand Casino: \r\n\r\n### Layout: \r\n\r\n> I haven't planned a specific idea for the layout of this board, but a\r\n> cool idea could be to structure it on a game you could see in a\r\n> casino. For example, it could take place on a roulette wheel/table or\r\n> craps table, or it could just be a regular casino where you can go\r\n> around and find Phil at different chance games.\r\n\r\n### Functionality:\r\n```\r\n\r\n#### Source 12\r\n```text\r\n\\- Horizons\r\n\r\n\\- Horizons presents interesting challenges as artists will need to\r\nthink in a unique way to model the environment in a way that is\r\ninteresting and visually appealing in an isometric style that's\r\ndifferent from the rest of the game\r\n\r\nFor Daniel: More information on specific implementation for these maps\r\ncan be found\r\n`UNKNOWN ARTICLE LINK: here`(https://docs.google.com/document/d/1rAI_9qNey9DkwZNg5QMCnG1M7zsGZ1p76OpjZo5g2b8/edit).\r\n\r\n##### Estimation for how much more/less time these maps might take compared to the base game: \r\n\r\n#### Minigame Assets  \r\n\r\n-   [Est. 35-40 minigames]\r\n```\r\n\r\n#### Source 13\r\n```text\r\n# Hard Stages: \r\n\r\n## Grand Clock Garage: \r\n\r\n###  Layout: \r\n\r\n> This stage takes place on the face of a giant grandfather clock under\r\n> repair. The spaces are arranged in two concentric circles, with the\r\n> inner circle slightly elevated. Connection from the outer ring to the\r\n> inner rings is either: 1) the minute hand of the clock 2) 4 paths\r\n> spaced at the 15 minute marks of the clock or 3) both. There are spots\r\n> on the edges of the clock where players can jump off and go shop or\r\n> avoid the clock hands moving (see functionality section).\r\n\r\n### Functionality:\r\n```\r\n\r\n#### Source 14\r\n```text\r\n**To Daniel:** Thanks for coming to fill in estimations. We went ahead\r\nand tried to get as much down as we could for art asset requirements,\r\nfeel free to add anything you think we might've missed or remove things\r\nthat won't be relevant. Each heading (minigame assets, character assets,\r\netc) should have a general time prediction. We went ahead and outlined a\r\nbasic methodology for art creation as well, feel free to adjust it based\r\non your own workflow or for each specific area (characters will most\r\nlikely require a different number of passes than entire maps).\r\n```\r\n\r\n#### Source 15\r\n```text\r\n2)  Should the toll of the trap be equivalent to the coins put in by a\r\n    player like the thwomp gates from more recent mario parties? In this\r\n    case, should the player just pay a custom price upon placing the\r\n    trap, instead of having 4 different items in a shop causing\r\n    confusion for the player?\r\n\r\n[Solution: Stops the player if they don\\'t want to pay 10 coins. If they\r\npay 10 coins it goes to the owner. This is a 1 time use item.]{.mark}\r\n\r\n## Pants on Fire:\r\n```\r\n\r\n#### Source 16\r\n```text\r\n-   Load Screen\r\n\r\n-   Multiplayer menu (with options for different modes)\r\n\r\n    -   Waiting to join/ queue menu\r\n\r\n    -   Join code generation/input menu to invite people via codes\r\n\r\n-   Workshop content menu (enable/disable/view mods)\r\n\r\n-   Battle Pass/Quest Menu\r\n\r\n    -   Cosmetic menu, to switch between cosmetics\r\n\r\n-   Map selection menu\r\n\r\n    -   Possible map settings menu (deciding what is enabled/disabled\r\n        for a game)\r\n\r\n    -   Character select menu\r\n\r\n-   Game summary screen, with game performance metrics\r\n\r\n-   Achievement progress menu [OPTIONAL]\r\n\r\n##### In Game:\r\n```\r\n\r\n#### Source 17\r\n```text\r\n-   Quality Assurance - 1 week\r\n\r\n-   Art Pass 3/Testing - 2 week\r\n\r\n-   Finalization - 1 week\r\n\r\n##### The hard ones: \r\n\r\n\\- Infinimap\r\n\r\n\\- Infinimap will need a set of modular assets you can use to construct\r\ndifferent pieces of the randomly generated map, will need a system to\r\napply subtle variation to each piece as well otherwise you would end up\r\nwith a lack of variation between pieces (prop scattering, subtle detail\r\ntextures, etc). Since it\\'s minecraft themed this will be much easier\r\nbut still present a unique set of objectives.\r\n\r\n\\- Horizons\r\n```\r\n\r\n#### Source 18\r\n```text\r\n-   ![image6.png](image6.png){width=\"6.267716535433071in\"\r\n    height=\"0.8611111111111112in\"}\r\n\r\n-   Possible foliage shader\r\n\r\n-   Possible fire/lava shader\r\n\r\n##### Shader Time Estimates: \r\n\r\n##### VFX \r\n\r\n-   Particles to add dynamic information\r\n\r\n-   Particles for various events\r\n\r\n-   Stars/Sparks/Halos for dice rolling and all kinds of stuff\r\n\r\n##### VFX Time Estimates: \r\n\r\n#### UI Assets: \r\n\r\n##### Out of game: \r\n\r\n-   Main Menu\r\n\r\n-   Options Menu\r\n\r\n-   Load Screen\r\n\r\n-   Multiplayer menu (with options for different modes)\r\n\r\n    -   Waiting to join/ queue menu\r\n```\r\n\r\n#### Source 19\r\n```text\r\n1.  If we wanted to have this tie into the casino theme that Top\r\n            Dog has going on right now. For example, a few months back I\r\n            suggested all items that modify your roll could be coins\r\n            that would be put in the slot machine. Another suggestion\r\n            could be all of the traps being **playing cards** that you\r\n            throw down on a space, with each card having the item icons\r\n            we already have made on them. [SOLUTION:]{.mark} It sounds\r\n            like we are going with casino chips of different colors and\r\n```\r\n\r\n#### Source 20\r\n```text\r\n### Layout: \r\n\r\n> The layout for this stage could be completely generic. I am not quite\r\n> sure how it would look since we haven't flushed out our ideas for\r\n> other stages yet, but once other stages are done we could get back to\r\n> this, as it may need to be designed specifically around all of the\r\n> stages. One definite space we need is a spot for the host of the game\r\n> to stand on, maybe in the middle, that players can use to talk to the\r\n> host and activate the map's main functionality.\r\n\r\n### Functionality:\r\n```"
};

export default spot_the_difference;