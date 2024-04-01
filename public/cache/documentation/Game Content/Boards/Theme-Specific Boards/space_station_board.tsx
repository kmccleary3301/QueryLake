
const space_station_board = {
	"slug": "Space Station Board",
	"content": "## Overview\r\n\r\nThe Space Station Board in \"Top Dog\" is a game map with mechanics similar to Mario Party, set in a space environment, where players navigate through various spaces that trigger in-game events.\r\n\r\n## Main Features\r\n\r\n- **Zero-Gravity Areas**: Altering the movement mechanics from normal to floating in designated sections of the board.\r\n- **Airlocks and Transport Tubes**: Functional elements that move players around the board.\r\n- **Board Events**: Events that affect gameplay are tied to specific board spaces.\r\n- **Technological Traps**: Traps that players can set, impacting the board or specific areas.\r\n\r\n## Concept Art\r\n\r\nConcept sketches convey the theme and layout of the Space Station Board, showcasing the central hub, crew quarters, and laboratory areas. The art emphasizes the feeling of isolation in space with a competitive play environment. Concept art and mood boards can be accessed for further information. `GAME FILE LINK: topdog_spacestation_moodboard.pdn`\r\n\r\n## Music and Audio\r\n\r\nThe board features its own ambient soundtrack, complemented by sound effects corresponding to high-tech surroundings such as airlocks and computer systems. More details on music themes can be found in the relevant files/folders. `GAME FILE LINK: Boards/Space Station/Music/`\r\n\r\n## Relevant Files/Folders\r\n\r\n- Concept Art: `GAME FILE LINK: topdog_spacestation_moodboard.pdn`\r\n- Music Themes: `GAME FILE LINK: Boards/Space Station/Music/`\r\n- Board Events: `GAME FILE LINK: Development/Board Logic`\r\n\r\n## See Also\r\n\r\n- [General Board Features](/docs/game_content/boards/general_board_features)\r\n- [Space Station Critters](/docs/game_content/critters/board_specific_critters/space_station_critters)\r\n- [Board Events and Gimmicks](/docs/game_content/boards/board_events_and_gimmicks)\r\n\r\n## Developer Notes\r\n\r\n\"The Space Station Board is designed to be a strategic challenge, utilizing the board's unique mechanics for efficient navigation and obstacle management.\"\r\n\r\n## Cited Document Text Segments\r\n\r\n#### Source 1\r\n```text\r\n\\- Allow selling items back for coins\r\n\r\n\\- Possible to increase max number of held items\r\n\r\n\\### Items\r\n\r\n\\- Unique items for each board\r\n\r\n\\- Powerful items that gain strength over time\r\n\r\n\\- Allow only 1 item used per turn\r\n\r\n\\### Boards\r\n\r\n\\- Ideas discussed for spaces similar to Mario Party boards\r\n\r\n\\- Blue Space\r\n\r\n\\- Red Space\r\n\r\n\\- Event Space\r\n\r\n\\- Star Space\r\n\r\n\\- Orb Space\r\n\r\n\\- Traps able to be placed on spaces\r\n\r\n\\- Dynamic music changes based on location on board\r\n\r\n\\### Stars\r\n\r\n\\- Collect golden bones as the \\\"star\\\" equivalent\r\n\r\n\\### Mini-games\r\n```\r\n\r\n#### Source 2\r\n```text\r\n\\## Concerns\r\n\r\n\\- Recent changes to Unity licensing fees may force switch to Unreal\r\n\r\n\\- Original name \\\"Top Dog\\\" already in use by another game\r\n\r\nHere are more details on the gameplay and technology for Top Dog:\r\n\r\n\\# Gameplay\r\n\r\n\\## Boards\r\n\r\n\\- Boards are the main game map, with a path that loops around similar\r\nto Mario Party\r\n\r\n\\- Spaces on the boards trigger events when landed on:\r\n\r\n\\- Blue spaces give coins\r\n\r\n\\- Red spaces take coins\r\n\r\n\\- Chance spaces trigger random events\r\n\r\n\\- Boss spaces initiate a boss mini-game\r\n\r\n\\- Shop spaces allow item purchases\r\n\r\n\\- Star spaces let you collect stars\r\n```\r\n\r\n#### Source 3\r\n```text\r\n\"ClubClubBug.png\" Some initial still image for Antony\r\n\r\n\"ClubClubFox.png\" Some initial still image for Fox\r\n\r\n\"Character Lineup.png\" A still image showing off the whole cast of Top\r\nDog characters side by side\r\n\r\nFollowing these images are 4 images for space icons that could be put\r\nonto the board as spaces players could walk over.\r\n\r\nFollowing these images are 3 concept art images for the Space Station, a\r\nboard that players could play on\r\n\r\nThere are 4 images showcasing possible Griffin Games logos, each\r\nprogressing to a more specific logo idea\r\n```\r\n\r\n#### Source 4\r\n```text\r\n> different items/event spaces do different stuff. I know it sounds\r\n> hard, but if we made the map super generic it could work. If every\r\n> board had a different event space action, for example, every time the\r\n> board switches, we just switch the event space to do what it would\r\n> have done on the board that was switched to.\r\n```\r\n\r\n#### Source 5\r\n```text\r\n\\# Game Scenes\r\n\r\n\\## Board\r\n\r\n\\- Using Cinemachine for camera movement\r\n\r\n\\- Board contains spaces the players move through\r\n\r\n\\- Spaces have different types that determine their function\r\n\r\n\\- Players earn coins by landing on certain spaces\r\n\r\n\\- Players have inventories to hold items\r\n\r\n\\- Items can modify dice rolls\r\n\r\n\\- Working on allowing stacking of item effects\r\n\r\n\\## Minigames\r\n\r\n\\- Quickdraw implemented\r\n\r\n\\- Asteroids uses new input system\r\n\r\n\\- Squid game red light green light\r\n\r\n\\- Using scene manager and state manager to transition between board and\r\nminigames\r\n\r\n\\# Multiplayer\r\n```\r\n\r\n#### Source 6\r\n```text\r\nClyde_Icon_Simple (1).png\r\n\r\nClyde_Character_Icon.png\r\n\r\nCatherine_Icon_Simple.png\r\n\r\n### DougModelReal \r\n\r\nAn animation file for doug\r\n\r\nDougModelReal - SampleScene - Windows\\_ Mac\\_ Linux - Unity 2021.3.1f1\r\nPersonal \\_DX11\\_ 2022-05-24 12-46-32\r\n\r\n## Boards \r\n\r\n### Wetworld \r\n\r\nMusic files for Wetworld:\r\n\r\n\\\"Water World Demo 1.wav\\\"\r\n\r\n\\\"Water World Demo 2.wav\\\"\r\n\r\n\\\"Water World Demo 3.wav\\\"\r\n\r\n### Universal Board Icons \r\n\r\nSpaceProtoRed.png\r\n\r\nSpaceProtoOrbGif.gif\r\n\r\nSpaceProtoHappen.jpeg\r\n\r\nSpaceProtoBlue.png\r\n\r\nDice Spin Concept.png\r\n\r\n### Space Station \r\n\r\nThese are mockups for the outside view of the space station\r\n```\r\n\r\n#### Source 7\r\n```text\r\nUse visual effects to highlight the different locations\r\n\r\nPan up from Wetworld to the Enchanted Forest.\r\n\r\nPan up from Enchanted Forest to Space Station.\r\n\r\nOr maybe pan down from Space Station to Wetworld\r\n\r\n0:30 - 0:45: Show gameplay snippets of maps\r\n\r\nShowcase board events\r\n\r\nShow new item shop mechanics\r\n\r\nemphasis on Enchanted Forest\r\n\r\n0:45 - 0:55: Demonstrate minigames.\r\n\r\nShow all 6 minigames\r\n\r\n0:55 - 1:00: Show off game stats\r\n\r\nNum of minigames\r\n\r\nNum of boards\r\n\r\nNum of characters\r\n\r\n1:20 - 1:30: Demonstrate character creation\r\n```\r\n\r\n#### Source 8\r\n```text\r\n##  \r\n\r\n## Phil Actions \r\n\r\nThese are what Phil can do when you land on one of his spaces.\r\n\r\n# What does Phil do \r\n\r\n-   Land on his space what happens?\r\n\r\n-   Lost half your coins\r\n\r\n-   Lose a star\r\n\r\n-   Return to the start\r\n\r\n-   Revolution / communism\r\n\r\n-   Get the bomb item\r\n\r\n-   Group minigame\r\n\r\n    -   Penalty for losing can be 10 coins, 20 coins, half coins, or a\r\n        star\r\n\r\n-   Phil Takeover\r\n\r\n    -   3 random blue/red spaces are turned into Phil spaces. These\r\n        spaces are returned to normal if landed on.\r\n```\r\n\r\n#### Source 9\r\n```text\r\n## Roll Booster \r\n\r\nCan roll higher than highest allowed value for a few turns\r\n\r\n## [Flip flop / rewind]{.mark} \r\n\r\n[Change direction of the board (like whistle in MP)]{.mark}\r\n\r\n## [Growth Item]{.mark} \r\n\r\n[Starts as a 1-3 die and gains 1-3 spaces each turn]{.mark}\r\n\r\n## [Quick Spender]{.mark} \r\n\r\n[Starts high and loses spaces over time]{.mark}\r\n\r\n## [Polarity Inverter]{.mark} \r\n\r\n[Reverses positive and negative values of board spaces]{.mark}\r\n\r\n## [Unique Duplicate]{.mark} \r\n\r\n[Choose an opponent, gain a copy of their chosen item]{.mark}\r\n\r\n# Forest Specific \r\n\r\n## [Stun spore hat (2 Votes)]{.mark}\r\n```\r\n\r\n#### Source 10\r\n```text\r\n> there is a ring in the middle you get sent into if you are unlucky\r\n> enough to land on event spaces near it. You are forced to walk around\r\n> a circle of red spaces until you are lucky enough to land on an event\r\n> space inside the circle to get you out.). We could have Phil placing\r\n> phil spaces in front of players, or doing more bad events than usual\r\n> to really give this board a \"the casino is rigged against you\"\r\n> feeling.\r\n```\r\n\r\n#### Source 11\r\n```text\r\n#### Icons \r\n\r\nThese are icons for the tavern/shop that can appear on the map\r\n\r\nTavern_Icon_V2.png\r\n\r\nTavern_Icon_V1.png\r\n\r\nAcorn_Concept.png\r\n\r\n#### Concept Art \r\n\r\nA bunch of.png images and .pdf storyboards mocking up various parts of\r\nthe Enchanted Forest\r\n\r\n#### Board Concept \r\n\r\n\\\"Enchanted Forest board.PNG\\\" is an image showcasing the board\r\nstructure\r\n\r\n\\\"Heatmap.png\\\" is an image showcasing the frequency each space is\r\nlanded on.\r\n\r\n### Board Ideas \r\n\r\nThis is a document with some ideas for boards.\r\n\r\n# Easy Stages: \r\n\r\n# Medium Stages: \r\n\r\n## Phil's Grand Casino: \r\n\r\n### Layout:\r\n```\r\n\r\n#### Source 12\r\n```text\r\n\\- Elevator\r\n\r\n\\- Travel from ground to canopy\r\n\r\n\\- Lanterns\r\n\r\n\\- Light paths at night\r\n\r\n\\# Development Notes\r\n\r\n\\- Using Blender for 3D modeling\r\n\r\n\\- Baking lighting from Blender into Unity\r\n\r\n\\- Imported map blockout into Unity\r\n\r\n\\- Discussions around day/night cycles\r\n\r\n\\- Considered moving parts in environment\r\n\r\n\\- Planning main menu set in studio space\r\n\r\n\\- Developing custom board system\r\n\r\n\\- Created icon designs for shop spaces\r\n\r\n\\- Modeling 3D board space markers\r\n\r\n\\# Meeting Notes\r\n\r\n\\- Regular meetings to review progress\r\n\r\n\\- Provided feedback on blockout, textures, modeling\r\n```\r\n\r\n#### Source 13\r\n```text\r\n\\- Danny said on 4/16/22 that he wouldn\\'t be opposed to a beach world\r\nseparate from Wetworld\r\n\r\n\\### Characters\r\n\r\n\\- On 12/16/22, Konari said he started working on rough concepts for\r\nNPCs in Wetworld after speaking with Danny, and planned to work on them\r\nmore after taking time to decompress from a funeral\r\n\r\n\\## Space Station\r\n\r\n\\### Concept Art\r\n\r\n\\- On 3/24/22, Daniel shared some of Konari\\'s Space Station concept art\r\n\r\n\\- On 4/1/22, Konari shared a cleaner, more traditional station layout\r\nthat kept a similar layout but looked more believable as a game map\r\n```\r\n\r\n#### Source 14\r\n```text\r\n-   Could target players trap spaces and turn them into Phil traps\r\n        (not phil spaces) that have negative effects.\r\n\r\n-   Next golden bone costs double.\r\n\r\n-   Lost half your stars (late game possibly), maybe scales as a fixed\r\n    amount\r\n\r\n-   Next movement, player stops and trigger the next trap space they\r\n    walk over\r\n\r\n-   If a player has 0 coins, they get x coins\r\n\r\nGriffin Games\\\r\nTop Dog: Phil Space Actions\r\n\r\nMinigame to steal coins\r\n\r\n-   3v1 where either 3 get to steal coins from 1\r\n\r\n3v1 Battle Minigame\r\n\r\n-   3s put up 20 coins each and 1 puts up 60\r\n\r\nCoin communism\r\n\r\nLiquidate Assets\r\n```\r\n\r\n#### Source 15\r\n```text\r\nBecause of this back and forth process, songs can take a while before\r\nthey become finalized.\r\n\r\nMusic for boards\r\n\r\n-   We will need a unique music track for each board, so 8 unique music\r\n    tracks total. **(4 weeks each track, 32 weeks total)**\r\n\r\n-   In order to implement dynamic music for these boards, we will need\r\n    some extra time to make up the variations of these themes. **(2\r\n    weeks each board, 16 weeks total)**\r\n\r\nMain theme music\r\n\r\n-   An iconic tune that is instantly recognizable as being the theme for\r\n    Top Dog. **(6 weeks)**\r\n\r\nMinigame Guide music\r\n```\r\n\r\n#### Source 16\r\n```text\r\n**Space Station Critters**\r\n\r\n**Aerojellies:** Mysterious jellyfish-like creatures that float about in\r\nspace. Their bodies are made of an extremely low density material and\r\nthey do not behave with any understood intelligence. Rumors say that the\r\nqueen of these strange critters lies somewhere hidden in space.\r\n\r\n## Animations \r\n\r\n### Universal \r\n\r\nDust cloud images used for walking animation\r\n\r\n\\\"Dust Cloud Tail Real.png\\\"\r\n\r\n\\\"Dust Cloud Tail.png\\\"\r\n\r\n\\\"Dust Cloud.png\\\"\r\n\r\n### DougModelReal \r\n\r\nThis is a folder for a Unity project that has some tests for the Doug\r\nmodel.\r\n\r\n## Prototypes\r\n```\r\n\r\n#### Source 17\r\n```text\r\n\\- Boss spaces initiate a boss mini-game\r\n\r\n\\- Shop spaces allow item purchases\r\n\r\n\\- Star spaces let you collect stars\r\n\r\n\\- Players take turns moving around the board and triggering events\r\n\r\n\\- After each turn, a short mini-game takes place\r\n\r\n\\## Mini-Games\r\n\r\n\\- Short competitive mini-games happen after every turn\r\n\r\n\\- Mini-games test skills like precision, speed, memory, etc\r\n\r\n\\- Outcome determines rewards like coins and stars\r\n\r\n\\- Mini-game themes planned:\r\n\r\n\\- Quickdraw duel\r\n\r\n\\- 2D platformer\r\n\r\n\\- Asteroid shooter\r\n\r\n\\- Squid game parody\r\n\r\n\\- Falling platforms\r\n```\r\n\r\n#### Source 18\r\n```text\r\n\\## Planning\r\n\r\n\\- Effort estimation needed for tasks\r\n\r\n\\- Scheduling Kickstarter campaign\r\n\r\n\\- Financial plans and projections\r\n\r\n\\## Code\r\n\r\n\\- Currently working on minigame code\r\n\r\n\\- Planning online multiplayer\r\n\r\n\\## Community Building\r\n\r\n\\- Working to gain control of r/TopDog subreddit\r\n\r\n\\- Planning social media presence\r\n\r\nWetworld and Space Station\r\n\r\nHere are detailed notes from the Wetworld and Space Station chat\r\nexports, organized into relevant categories and subcategories:\r\n\r\n\\## Wetworld\r\n\r\n\\### Concept Art\r\n```\r\n\r\n#### Source 19\r\n```text\r\n> location it has teleported to. Going to Wet World may sink parts of\r\n> the map in water, which can be used to trap opponents in bad\r\n> situations. Going to Enchanted forest would put the golden acorn\r\n> mechanic into place along with the witch, etc. On top of this, item\r\n> shops (which don't change places) will sell the board specific items\r\n> of the place they have teleported to.\r\n>\r\n> I came up with this idea while making the board simulator,\r\n> specifically when I set up an enum to differentiate boards that sell\r\n> different items/event spaces do different stuff. I know it sounds\r\n```\r\n\r\n#### Source 20\r\n```text\r\nDice Spin Concept.png\r\n\r\n### Space Station \r\n\r\nThese are mockups for the outside view of the space station\r\n\r\n\\\"Topdog_spacestation_moodboard.pdn\\\"\r\n\r\n\\\"outside-sketch.jpg\\\"\r\n\r\n\\\"outside-sketch2.jpg\\\"\r\n\r\n\\\"outside-sketch3.jpg\\\"\r\n\r\n### Enchanted Forest \r\n\r\n#### Tavern Area Art Pass \r\n\r\nA bunch of images with mockups for the tavern area\r\n\r\n#### Music \r\n\r\nForrest Music\\_ Demo 4 Newest Tempo.wav\r\n\r\nForrest Music\\_ Demo 3 Drums.wav\r\n\r\nForrest Music\\_ Demo 2 Excited.wav\r\n\r\nForrest Music\\_ Demo 1.wav\r\n\r\n#### Icons \r\n\r\nThese are icons for the tavern/shop that can appear on the map\r\n\r\nTavern_Icon_V2.png\r\n\r\nTavern_Icon_V1.png\r\n```"
};

export default space_station_board;