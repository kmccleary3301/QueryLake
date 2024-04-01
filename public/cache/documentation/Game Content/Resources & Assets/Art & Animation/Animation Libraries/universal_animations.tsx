
const universal_animations = {
	"slug": "Universal Animations",
	"content": "Universal animations are integral to Top Dog, providing a consistent set of movements for all characters to maintain a cohesive game standard.\r\n\r\n## Animation Libraries\r\n\r\nThe Top Dog animation library includes:\r\n\r\n- Idle Animations\r\n- Walking/Running Cycles\r\n- Jumping Sequences\r\n- Interaction Animations \r\n\r\n## Development Workflow\r\n\r\nThis approach allows for efficient use of resources and consistent character movement.\r\n\r\n## Relevant Files/Folders\r\n\r\n- Character Animation Prototypes: ``GAME FILE LINK: Animations/DougModelReal``\r\n- Universal Animation Assets: ``GAME FILE LINK: Animations/Universal Animations``\r\n\r\n## See Also\r\n\r\n- [[Playable Characters]]\r\n- [[Non-Playable Characters]]\r\n- [[Items & Power-Ups]]\r\n- [[Art & Animation]]\r\n- [[Programming & Coding]]\r\n- [[Testing & Quality Assurance]]\r\n\r\n## Developer Notes\r\n\r\n### Dust Clouds\r\n\r\nFor walking or running animations, integrate the following dust cloud images:\r\n\r\n- ``GAME FILE LINK: Dust Cloud Tail Real.png``\r\n- ``GAME FILE LINK: Dust Cloud Tail.png``\r\n- ``GAME FILE LINK: Dust Cloud.png``\r\n\r\n### Animation Consistency\r\n\r\nRegularly review and update the animation library to resolve any inconsistencies and improve the quality.\r\n\r\n## Cited Document Text Segments\r\n\r\n#### Source 1\r\n```text\r\n-   Mini game animations (ex: Free-for-all games with an npc\r\n            badie)\r\n\r\n-   Create root motion animations for all animated map assets (**3 - 5\r\n    hours per asset**)\r\n\r\n    -   Plants\r\n\r\n    -   Events\r\n\r\n```{=html}\r\n<!-- -->\r\n```\r\n-   Create blend trees and animation transitions for each animation set\r\n    to blend between animations (**5 - 10 hours per animation set** )\r\n\r\n-   ![image10.png](image10.png){width=\"3.588542213473316in\"\r\n    height=\"1.2206550743657043in\"}\r\n\r\n-   Cleaning up animations and QA (**1-5 hours per asset**)\r\n\r\n##### Animation Time Estimates\r\n```\r\n\r\n#### Source 2\r\n```text\r\n-   Create root motion and base animations for all playable characters\r\n    (**3-5 days per character**)\r\n\r\n    -   Walk\r\n\r\n    -   Run\r\n\r\n    -   Idle\r\n\r\n    -   Jump\r\n\r\n    -   Action group\r\n\r\n        -   Mini game specific animations (ex: throw, hit, steer)\r\n\r\n        -   Board animations (ex: using items)\r\n\r\n-   Create root motion animations for all NPCs (**3-5 days per NPC**)\r\n\r\n    -   Walk\r\n\r\n    -   Run\r\n\r\n    -   Idle\r\n\r\n    -   Jump\r\n\r\n    -   Action animations\r\n\r\n        -   Board animations (ex: selling items)\r\n\r\n        -   Mini game animations (ex: Free-for-all games with an npc\r\n            badie)\r\n```\r\n\r\n#### Source 3\r\n```text\r\n-   Cleaning up animations and QA (**1-5 hours per asset**)\r\n\r\n##### Animation Time Estimates \r\n\r\n-   Base Animation for PC: **4-6 weeks**\r\n\r\n-   Base Animation for NPC: **4-6 weeks**\r\n\r\n-   Base Animations for map assets: **2-3 weeks**\r\n\r\n-   Blend Trees and transitions: **4-6 weeks**\r\n\r\n-   QA and clean up: **3-4 weeks**\r\n\r\n-   **Total 17-24 weeks**\r\n\r\n### **Music** \r\n\r\nAll music will undergo the following processes:\r\n\r\n1.  Ideation.\r\n\r\n    a.  This might involve creating a bunch of small music segments to\r\n        experiment with the correct sound we\\'re looking for.\r\n\r\n2.  Rough Draft\r\n```\r\n\r\n#### Source 4\r\n```text\r\n>\r\n> `UNKNOWN ARTICLE LINK: Workshop Assets:`(#workshop-assets)\r\n>\r\n> [[Workshop Template Time\r\n> Estimate:]](#workshop-template-time-estimate)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Animation:`(#animation)\r\n>\r\n> [[Animation Time Estimates [Total: 17-24\r\n> weeks]]](#animation-time-estimates)\r\n```\r\n\r\n#### Source 5\r\n```text\r\n\\- Menus styled as backstage rooms\r\n\r\n\\- Dice roll animations\r\n\r\n\\- Gashapon capsule animations\r\n\r\n\\### Characters\r\n\r\n\\- Gender neutral animal characters\r\n\r\n\\- Custom characters\r\n\r\n\\### Music\r\n\r\n\\- Adaptive music changes based on location\r\n\r\n\\- Music inspired by Mario Party soundtracks\r\n\r\n\\### Art Style\r\n\r\n\\- Anthropomorphic animal characters\r\n\r\n\\## Development\r\n\r\n\\### Platforms\r\n\r\n\\- Primarily PC with controller support\r\n\r\n\\- Use WASD keyboard buttons displayed in prompts\r\n\r\n\\### Testing\r\n\r\n\\- Find experienced playtesters\r\n\r\n\\- Seek out YouTubers/streamers\r\n\r\nHere are my detailed notes on the game development chat log:\r\n```\r\n\r\n#### Source 6\r\n```text\r\n-   `UNKNOWN ARTICLE LINK: https://rivals-of-aether.fandom.com/wiki/Sandbert`(https://rivals-of-aether.fandom.com/wiki/Sandbert)\r\n\r\nIf this proves to be too difficult our workshop example could be\r\nexisting content from the game\r\n\r\n##### Workshop Template Time Estimate: \r\n\r\n#### Animation: \r\n\r\n-   Organize using state machines to keep animation workflow clean\r\n    between layers, example image of using Airborne and Running state\r\n    machines to keep like animations organized\r\n\r\n![image8.png](image8.png)\r\n\r\n-   Create root motion and base animations for all playable characters\r\n    (**3-5 days per character**)\r\n\r\n    -   Walk\r\n```\r\n\r\n#### Source 7\r\n```text\r\n\\- Can spawn random biome prefabs\r\n\r\n\\- Used for quickly creating backdrops\r\n\r\n\\# Animations\r\n\r\n\\- Created animations for walking, jumping, idling\r\n\r\n\\- Footstep logic checks terrain type and plays appropriate sounds\r\n\r\n\\- Working on blending multiple animations together\r\n\r\n\\# AI System\r\n\r\n\\- Behavior trees implemented for AI decision making\r\n\r\n\\# User Interface\r\n\r\n\\- Character selection screen design in Figma\r\n\r\n\\- In-game UI displays player scores, items\r\n\r\n\\# Visuals\r\n\r\n\\- Using Universal Render Pipeline (URP)\r\n\r\n\\- Custom shaders created:\r\n\r\n\\- Vertex color\r\n\r\n\\- Outline\r\n\r\n\\- Dual-sided\r\n\r\n\\- Fresnel\r\n\r\n\\- Splatmap\r\n```\r\n\r\n#### Source 8\r\n```text\r\n**Space Station Critters**\r\n\r\n**Aerojellies:** Mysterious jellyfish-like creatures that float about in\r\nspace. Their bodies are made of an extremely low density material and\r\nthey do not behave with any understood intelligence. Rumors say that the\r\nqueen of these strange critters lies somewhere hidden in space.\r\n\r\n## Animations \r\n\r\n### Universal \r\n\r\nDust cloud images used for walking animation\r\n\r\n\\\"Dust Cloud Tail Real.png\\\"\r\n\r\n\\\"Dust Cloud Tail.png\\\"\r\n\r\n\\\"Dust Cloud.png\\\"\r\n\r\n### DougModelReal \r\n\r\nThis is a folder for a Unity project that has some tests for the Doug\r\nmodel.\r\n\r\n## Prototypes\r\n```\r\n\r\n#### Source 9\r\n```text\r\n\\- Timelapses of character art are mentioned to be recorded\r\n\r\n\\- Character animations like idle animations are worked on\r\n\r\nEnvironments:\r\n\r\n\\- Enchanted Forest environment art style is discussed extensively\r\n\r\n\\- Inspired by Paper Mario and Pikmin environments\r\n\r\n\\- Uses pixel art, sprite cards, simple textures\r\n\r\n\\- Vertex painting for lighting/shading\r\n\r\n\\- Modular foliage and buildings\r\n\r\n\\- Space Station environment moodboarding and concepts\r\n\r\n\\- Discussions on using orange, blue, white color schemes\r\n\r\n\\- Different spacesuit designs for inside vs outside station\r\n```\r\n\r\n#### Source 10\r\n```text\r\nClyde_Icon_Simple (1).png\r\n\r\nClyde_Character_Icon.png\r\n\r\nCatherine_Icon_Simple.png\r\n\r\n### DougModelReal \r\n\r\nAn animation file for doug\r\n\r\nDougModelReal - SampleScene - Windows\\_ Mac\\_ Linux - Unity 2021.3.1f1\r\nPersonal \\_DX11\\_ 2022-05-24 12-46-32\r\n\r\n## Boards \r\n\r\n### Wetworld \r\n\r\nMusic files for Wetworld:\r\n\r\n\\\"Water World Demo 1.wav\\\"\r\n\r\n\\\"Water World Demo 2.wav\\\"\r\n\r\n\\\"Water World Demo 3.wav\\\"\r\n\r\n### Universal Board Icons \r\n\r\nSpaceProtoRed.png\r\n\r\nSpaceProtoOrbGif.gif\r\n\r\nSpaceProtoHappen.jpeg\r\n\r\nSpaceProtoBlue.png\r\n\r\nDice Spin Concept.png\r\n\r\n### Space Station \r\n\r\nThese are mockups for the outside view of the space station\r\n```\r\n\r\n#### Source 11\r\n```text\r\n![image12.png](image12.png)\r\n\r\n**Character Selection (With\r\nExamples)**![image1.png](image1.png)\r\n\r\n![image5.png](image5.png)\r\n\r\n### Prototype Videos \r\n\r\n\\\"Top-dog-animation-test.mp4\\\" is a video showcasing Doug with\r\nanimations moving across the Zelda map.\r\n\r\n\\\"Witch\\'s Hut.mov\\\" is a video showcasing the Witch\\'s Hut in action on\r\nthe Zelda prototype map\r\n\r\n## Music \r\n\r\n\\\"Wonderful6.m4a\\\" is a music file written by Danny\\'s friend for a\r\npotential song theme for the game\r\n\r\n## Budget & Schedule. \r\n\r\nThis is a document we made to try and think about how long and costly\r\nmaking a Kickstarter trailer would be.\r\n\r\nGriffin Games Budget & Schedule\r\n```\r\n\r\n#### Source 12\r\n```text\r\n\\- Different spacesuit designs for inside vs outside station\r\n\r\n\\- Screenshots rendered of environments to showcase art\r\n\r\n\\- Both day and night time versions\r\n\r\n\\- With and without board spaces\r\n\r\n\\- Discussions on lighting and halo effects\r\n\r\nMinigames:\r\n\r\n\\- No Cakewalk\r\n\r\n\\- Cake environment design and decorations\r\n\r\n\\- Glass bridge modeling and breaking animations\r\n\r\n\\- Camera angles and banners discussed\r\n\r\n\\- Failing Upwards\r\n\r\n\\- Modular building pieces for procedural generation\r\n\r\n\\- Small tricky platforms like AC units\r\n\r\n\\- Overall theming and modeling\r\n\r\n\\- Bandstand\r\n\r\n\\- Theater curtain animation\r\n```\r\n\r\n#### Source 13\r\n```text\r\n\\### Stars\r\n\r\n\\- Collect golden bones as the \\\"star\\\" equivalent\r\n\r\n\\### Mini-games\r\n\r\n\\- Shell game where players try to avoid picking cup with ball\r\n\r\n\\- Western duel/quick draw mini-game\r\n\r\n\\- Rhythm game with button prompts\r\n\r\n\\- Memory game with counting objects\r\n\r\n\\- Cooking mechanic to combine items\r\n\r\n\\- First-person shooter with silly weapons\r\n\r\n\\- Falling rock dodge game\r\n\r\n\\- Robot racing game\r\n\r\n\\- Pod racing game\r\n\r\n\\## Visuals\r\n\r\n\\### UI\r\n\r\n\\- Main menu as town square area\r\n\r\n\\- Menus styled as backstage rooms\r\n\r\n\\- Dice roll animations\r\n\r\n\\- Gashapon capsule animations\r\n\r\n\\### Characters\r\n```\r\n\r\n#### Source 14\r\n```text\r\n\\- Mushroom creature\r\n\r\n\\- Tree creature\r\n\r\n\\# Art & Animation\r\n\r\n\\## Concept Art\r\n\r\n\\- Shopkeepers\r\n\r\n\\- Host\r\n\r\n\\- Monster characters\r\n\r\n\\- Enchanted forest environments\r\n\r\n\\## Character Art\r\n\r\n\\- 2D character sprites\r\n\r\n\\- 3D character models\r\n\r\n\\- Animations\r\n\r\n\\## Environment Art\r\n\r\n\\- 3D environments for Enchanted Forest board\r\n\r\n\\- 3D environments for minigame arenas\r\n\r\n\\- Props\r\n\r\n\\# Music & Audio\r\n\r\n\\- Looking for music partners\r\n\r\n\\- Discussed deals with Jack and SMLE (electronic artist duo)\r\n\r\n\\- Sound effects\r\n\r\n\\- Voice acting\r\n\r\n\\# Gameplay\r\n\r\n\\## Enchanted Forest Board\r\n\r\n\\- Main board game component with multiple paths\r\n```\r\n\r\n#### Source 15\r\n```text\r\n### View this doc alongside the Approved Item spreadsheet \r\n\r\n### Important points highlighted blue \r\n\r\n### Balance Concerns in red \r\n\r\n### Points not highlighted would be nice to have feedback on, but not necessary \r\n\r\n# Universal Items \r\n\r\n## Phil's Bomb:\r\n```\r\n\r\n#### Source 16\r\n```text\r\nc.  A grand theme that plays if the player has won the entire game.\r\n        (example:\r\n        `UNKNOWN ARTICLE LINK: https://www.youtube.com/watch?v=c2FesrskB_g`(https://www.youtube.com/watch?v=c2FesrskB_g)\r\n        )\r\n\r\n3.  Character Victory Themes\r\n\r\n    a.  A short jingle that plays for the character if they've won the\r\n        match\r\n\r\nThere is also an excel document that lists these items out.\r\n\r\n## Items \r\n\r\n### Universal Items \r\n\r\nThese are the item images for all of the planned items we have so far.\r\n\r\nWarp_Trap.png\r\n\r\nUniversal_Items.png\r\n\r\nUniversal_Items_2.png\r\n\r\nTriple_Up_Tennis_Ball_Item.png\r\n```\r\n\r\n#### Source 17\r\n```text\r\n##### Minigame Time Estimates: \r\n\r\n-   Blocking out/Testing -\r\n\r\n-   Art Pass 1/Testing -\r\n\r\n-   Art Pass 2/Testing -\r\n\r\n-   Quality Assurance -\r\n\r\n-   Art Pass 3/Testing -\r\n\r\n-   Finalization -\r\n\r\nTo Daniel: Minigames are a different beast than maps so feel free to\r\nre-draft the steps required for art passes if you'd like, adding less or\r\nmore.\r\n\r\n#### Character Assets \r\n\r\n-   10 Characters\r\n\r\n    -   Palette Swap Alternates\r\n\r\n    -   More Complex alternates (if we do some kind of skin/battle pass\r\n        idea)\r\n\r\n-   Animations for all characters\r\n\r\n##### Character Time Estimates: \r\n\r\n#### Shaders\r\n```\r\n\r\n#### Source 18\r\n```text\r\n#### Minigame Assets  \r\n\r\n-   [Est. 35-40 minigames]\r\n\r\n```{=html}\r\n<!-- -->\r\n```\r\n-   Video tutorial\r\n\r\n-   Written rule description as well as accompanying control icons\r\n\r\n-   Assets for the minigame (2D and 3D)\r\n\r\n-   Minigame specific UI\r\n\r\n-   Will vary dramatically on a case by case basis, as an example little\r\n    wars will require much more work than quickdraw asset wise (both\r\n    share a background but little wars will require four fully\r\n    functional troops with accompanying animations, effects, etc.)\r\n\r\n##### Minigame Time Estimates: \r\n\r\n-   Blocking out/Testing -\r\n\r\n-   Art Pass 1/Testing -\r\n```\r\n\r\n#### Source 19\r\n```text\r\n## Draco's Karma \r\n\r\nGive a player coins / items and get things back\r\n\r\n## [Finn's Wipeout]{.mark} \r\n\r\n[Reset everyone to the start of the board]{.mark}\r\n\r\n## Assemble Exodia \r\n\r\nStep on five specific squares on the map, steal a star from everyone\r\n\r\n### Confirmed Items \r\n\r\nThis is a list of items that have been confirmed\r\n\r\n# Universal \r\n\r\n## [Lavender:]{.mark} \r\n\r\n[landing on billy\\'s space drop this item to make Billy run away]{.mark}\r\n\r\n[1 time use]{.mark}\r\n\r\n## [Battal buzzer:]{.mark} \r\n\r\n[create a duel for coins/stars]{.mark}\r\n\r\n## [Reverse Mushroom:]{.mark}\r\n```\r\n\r\n#### Source 20\r\n```text\r\n# Universal \r\n\r\n## Wish bone: \r\n\r\nbreak it in half, get a chance to get extra coins after each task\r\n\r\n## [Wet Fish:]{.mark} \r\n\r\n[characters can\\'t land on same space who got slapped or pass\r\nthem]{.mark}\r\n\r\n[last 1 turn]{.mark}\r\n\r\n[can be used on self or others]{.mark}\r\n\r\n## [Shop Ticket:]{.mark} \r\n\r\n[Discount on next item you buy (50%, more or less depends on\r\nbalance)]{.mark}\r\n\r\n-   [Only appears in random orb spaces, can't buy in shop]{.mark}\r\n\r\n## [Game Chooser]{.mark} \r\n\r\n[Pick 2v2, FFA, 1v3, etc or choose 1 from a random 5]{.mark}\r\n\r\n## Roll Booster \r\n\r\nCan roll higher than highest allowed value for a few turns\r\n```"
};

export default universal_animations;