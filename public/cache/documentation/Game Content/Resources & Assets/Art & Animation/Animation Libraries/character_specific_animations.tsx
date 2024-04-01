
const character_specific_animations = {
	"slug": "Character Specific Animations",
	"content": "Character specific animations are crafted to align with individual backstories and characteristics, enhancing the unique identity of each character on screen.\r\n\r\n## Animation Libraries\r\n\r\nEach character’s library contains animations for movements, expressions, and interactions, ranging from idle postures to complex action sequences.\r\n\r\n## Implementation Process\r\n\r\nDevelopment stages include:\r\n\r\n1. **Conceptualization**: Designing character’s animation style based on their traits and narrative role.\r\n   \r\n2. **Motion Design**: Crafting movement sets such as walking and running cycles, reaction shots, and special moves.\r\n\r\n3. **Rigging and Skinning**: Character models are rigged and then the model's mesh is bound to the rig.\r\n\r\n4. **Keyframe Animation**: Setting keyframes to define rig positions and using interpolation for transitions.\r\n\r\n5. **Refinement**: Ensuring fluidity and coherence with other models and the game world. \r\n\r\n6. **Integration**: Incorporating animations into the game engine, triggered by events or player inputs.\r\n\r\n7. **Optimization**: Testing and optimizing for performance across platforms.\r\n\r\n## Playable Characters\r\n\r\nEach playable character, such as *[Doug](/docs/game_content/characters/playable_characters/doug)* and *[Catherine](/docs/game_content/characters/playable_characters/catherine)*, has exclusive animations reflecting their personalities.\r\n\r\n## Relevant Files/Folders\r\n\r\n- Character specific animation files: <|Animations/DougModelReal/Assets|.\r\n- Character modeling and rigging files: `GAME FILE LINK: Characters/Doug/DougModelLineupHD.png`.\r\n\r\n## See Also\r\n\r\n- [[Playable Characters]]\r\n\r\n## Developer Notes\r\n\r\n- \"Considering the compatibility of character specific animations with universal animations.\" - Dev Team Memo.\r\n- \"Approach to universal rigging structure for character specific animations needs reviewing.\" - Technical Meet Notes.\r\n\r\n## Cited Document Text Segments\r\n\r\n#### Source 1\r\n```text\r\n\\- Paulie - Food reviewer character\r\n\r\n\\- Clyde - Bounty hunter character\r\n\r\n\\### Custom Characters\r\n\r\n\\- Custom characters can be created and added to the game\r\n\r\n\\- Custom characters should have automatically generated trailer videos\r\nshowcasing them\r\n\r\n\\### Character Gender\r\n\r\n\\- Character bios do not specify gender\r\n\r\n\\- Use they/them pronouns for all characters\r\n\r\n\\### Character Items\r\n\r\n\\- Ideas for unique items for each character\r\n\r\n\\- Concerns raised about limiting powerful items to certain characters\r\n\r\n\\- Suggestion to have \\\"chosen items\\\" that any character can select\r\n\r\n\\## World/Setting\r\n```\r\n\r\n#### Source 2\r\n```text\r\n-   Create root motion and base animations for all playable characters\r\n    (**3-5 days per character**)\r\n\r\n    -   Walk\r\n\r\n    -   Run\r\n\r\n    -   Idle\r\n\r\n    -   Jump\r\n\r\n    -   Action group\r\n\r\n        -   Mini game specific animations (ex: throw, hit, steer)\r\n\r\n        -   Board animations (ex: using items)\r\n\r\n-   Create root motion animations for all NPCs (**3-5 days per NPC**)\r\n\r\n    -   Walk\r\n\r\n    -   Run\r\n\r\n    -   Idle\r\n\r\n    -   Jump\r\n\r\n    -   Action animations\r\n\r\n        -   Board animations (ex: selling items)\r\n\r\n        -   Mini game animations (ex: Free-for-all games with an npc\r\n            badie)\r\n```\r\n\r\n#### Source 3\r\n```text\r\n-   Mini game animations (ex: Free-for-all games with an npc\r\n            badie)\r\n\r\n-   Create root motion animations for all animated map assets (**3 - 5\r\n    hours per asset**)\r\n\r\n    -   Plants\r\n\r\n    -   Events\r\n\r\n```{=html}\r\n<!-- -->\r\n```\r\n-   Create blend trees and animation transitions for each animation set\r\n    to blend between animations (**5 - 10 hours per animation set** )\r\n\r\n-   ![image10.png](image10.png){width=\"3.588542213473316in\"\r\n    height=\"1.2206550743657043in\"}\r\n\r\n-   Cleaning up animations and QA (**1-5 hours per asset**)\r\n\r\n##### Animation Time Estimates\r\n```\r\n\r\n#### Source 4\r\n```text\r\n\\- Menus styled as backstage rooms\r\n\r\n\\- Dice roll animations\r\n\r\n\\- Gashapon capsule animations\r\n\r\n\\### Characters\r\n\r\n\\- Gender neutral animal characters\r\n\r\n\\- Custom characters\r\n\r\n\\### Music\r\n\r\n\\- Adaptive music changes based on location\r\n\r\n\\- Music inspired by Mario Party soundtracks\r\n\r\n\\### Art Style\r\n\r\n\\- Anthropomorphic animal characters\r\n\r\n\\## Development\r\n\r\n\\### Platforms\r\n\r\n\\- Primarily PC with controller support\r\n\r\n\\- Use WASD keyboard buttons displayed in prompts\r\n\r\n\\### Testing\r\n\r\n\\- Find experienced playtesters\r\n\r\n\\- Seek out YouTubers/streamers\r\n\r\nHere are my detailed notes on the game development chat log:\r\n```\r\n\r\n#### Source 5\r\n```text\r\n\\- Sprites imported into Unity\r\n\r\n\\## Version Control\r\n\r\n\\- GitHub used for source control and collaboration\r\n\r\n\\- Branches used for features in development\r\n\r\n\\## Multiplayer\r\n\r\n\\- Steam API powers online multiplayer\r\n\r\n\\- Built-in Unity networking handles local co-op\r\n\r\nIdeas Element Chat\r\n\r\nHere are detailed notes on the game ideas and discussion from the chat\r\nexport:\r\n\r\n\\## Characters\r\n\r\n\\### Existing Characters\r\n\r\n\\- Doug - Main character, has a golden bone collar\r\n\r\n\\- Catherine - Cat character\r\n\r\n\\- Paulie - Food reviewer character\r\n\r\n\\- Clyde - Bounty hunter character\r\n\r\n\\### Custom Characters\r\n```\r\n\r\n#### Source 6\r\n```text\r\n\\- Custom shaders created:\r\n\r\n\\- Vertex color\r\n\r\n\\- Outline\r\n\r\n\\- Dual-sided\r\n\r\n\\- Fresnel\r\n\r\n\\- Splatmap\r\n\r\n\\- Particle effects for trail FX\r\n\r\nArt Element Chat\r\n\r\nHere are my detailed notes on the game art chat:\r\n\r\nCharacters:\r\n\r\n\\- Several character designs and sketches are discussed, including:\r\n\r\n\\- Paulie (rabbit)\r\n\r\n\\- Phil (goat)\r\n\r\n\\- Host (lion) redesign with ringmaster look, salt and pepper mane\r\n\r\n\\- Frog characters with angry and relaxed poses\r\n\r\n\\- Chameleon character design\r\n\r\n\\- Character colors and outfits are discussed for various characters\r\n\r\n\\- Timelapses of character art are mentioned to be recorded\r\n```\r\n\r\n#### Source 7\r\n```text\r\n-   `UNKNOWN ARTICLE LINK: https://rivals-of-aether.fandom.com/wiki/Sandbert`(https://rivals-of-aether.fandom.com/wiki/Sandbert)\r\n\r\nIf this proves to be too difficult our workshop example could be\r\nexisting content from the game\r\n\r\n##### Workshop Template Time Estimate: \r\n\r\n#### Animation: \r\n\r\n-   Organize using state machines to keep animation workflow clean\r\n    between layers, example image of using Airborne and Running state\r\n    machines to keep like animations organized\r\n\r\n![image8.png](image8.png)\r\n\r\n-   Create root motion and base animations for all playable characters\r\n    (**3-5 days per character**)\r\n\r\n    -   Walk\r\n```\r\n\r\n#### Source 8\r\n```text\r\n\\- Mushroom creature\r\n\r\n\\- Tree creature\r\n\r\n\\# Art & Animation\r\n\r\n\\## Concept Art\r\n\r\n\\- Shopkeepers\r\n\r\n\\- Host\r\n\r\n\\- Monster characters\r\n\r\n\\- Enchanted forest environments\r\n\r\n\\## Character Art\r\n\r\n\\- 2D character sprites\r\n\r\n\\- 3D character models\r\n\r\n\\- Animations\r\n\r\n\\## Environment Art\r\n\r\n\\- 3D environments for Enchanted Forest board\r\n\r\n\\- 3D environments for minigame arenas\r\n\r\n\\- Props\r\n\r\n\\# Music & Audio\r\n\r\n\\- Looking for music partners\r\n\r\n\\- Discussed deals with Jack and SMLE (electronic artist duo)\r\n\r\n\\- Sound effects\r\n\r\n\\- Voice acting\r\n\r\n\\# Gameplay\r\n\r\n\\## Enchanted Forest Board\r\n\r\n\\- Main board game component with multiple paths\r\n```\r\n\r\n#### Source 9\r\n```text\r\nThere are 4 images showcasing possible Griffin Games logos, each\r\nprogressing to a more specific logo idea\r\n\r\nThere is a section for Concept Art images and videos, including but not\r\nlimited to: Early concepts for characters and the Enchanted Forest, art\r\nfor the critters that could appear in the world of Top Dog, rigging\r\nvideos for the character animations, Top Dog logo art, Host character\r\nand antagonist character art including the early concept art for Phil,\r\nand some shopkeeper art.\r\n```\r\n\r\n#### Source 10\r\n```text\r\nCharacter pictures or gifs, along with descriptions and storylines (good\r\nguys, villains, etc.) ● Character information\r\n\r\nWe can use our character bio doc for the 10 main characters.\r\n\r\nWe\\'ll need to work on getting some bios created for some of the main\r\nNPC characters.\r\n\r\nImportant note: We have a lot of content describing the gameplay, art,\r\ncharacters, and writing. But we\\'re missing music, which is a major\r\ncomponent of this game. Here are a couple ways we plan on using music to\r\nhelp our world come to life:\r\n\r\nAdaptive Music\r\n```\r\n\r\n#### Source 11\r\n```text\r\n\\- Announcements and events\r\n\r\n\\- Holiday/topical posts\r\n\r\n\\- Milestones and achievements\r\n\r\n\\- Gifs and short video clips\r\n\r\nExecutive Suite\r\n\r\nHere are my detailed notes on the relevant information from the chat\r\nlog:\r\n\r\n\\# Game Concept\r\n\r\n\\- Multiplayer party game with minigames and a board game component\r\n\r\n\\- Set in an enchanted forest with mystical characters\r\n\r\n\\## Other Characters\r\n\r\n\\- Shopkeepers (concept art done but unnamed)\r\n\r\n\\- Host character (concept art done but unnamed)\r\n\r\n\\- Monster characters\r\n\r\n\\- Mushroom creature\r\n\r\n\\- Tree creature\r\n\r\n\\# Art & Animation\r\n\r\n\\## Concept Art\r\n\r\n\\- Shopkeepers\r\n\r\n\\- Host\r\n```\r\n\r\n#### Source 12\r\n```text\r\n-   Cleaning up animations and QA (**1-5 hours per asset**)\r\n\r\n##### Animation Time Estimates \r\n\r\n-   Base Animation for PC: **4-6 weeks**\r\n\r\n-   Base Animation for NPC: **4-6 weeks**\r\n\r\n-   Base Animations for map assets: **2-3 weeks**\r\n\r\n-   Blend Trees and transitions: **4-6 weeks**\r\n\r\n-   QA and clean up: **3-4 weeks**\r\n\r\n-   **Total 17-24 weeks**\r\n\r\n### **Music** \r\n\r\nAll music will undergo the following processes:\r\n\r\n1.  Ideation.\r\n\r\n    a.  This might involve creating a bunch of small music segments to\r\n        experiment with the correct sound we\\'re looking for.\r\n\r\n2.  Rough Draft\r\n```\r\n\r\n#### Source 13\r\n```text\r\n##### Minigame Time Estimates: \r\n\r\n-   Blocking out/Testing -\r\n\r\n-   Art Pass 1/Testing -\r\n\r\n-   Art Pass 2/Testing -\r\n\r\n-   Quality Assurance -\r\n\r\n-   Art Pass 3/Testing -\r\n\r\n-   Finalization -\r\n\r\nTo Daniel: Minigames are a different beast than maps so feel free to\r\nre-draft the steps required for art passes if you'd like, adding less or\r\nmore.\r\n\r\n#### Character Assets \r\n\r\n-   10 Characters\r\n\r\n    -   Palette Swap Alternates\r\n\r\n    -   More Complex alternates (if we do some kind of skin/battle pass\r\n        idea)\r\n\r\n-   Animations for all characters\r\n\r\n##### Character Time Estimates: \r\n\r\n#### Shaders\r\n```\r\n\r\n#### Source 14\r\n```text\r\nNum of minigames\r\n\r\nNum of boards\r\n\r\nNum of characters\r\n\r\n1:20 - 1:30: Demonstrate character creation\r\n\r\nHave screen transition from drawing a character to the character being\r\nplayable and moving in the game.\r\n\r\nSome kind of visual indicator like a watch to make it more clear the\r\ncharacters are the same.\r\n\r\n1:30: End\r\n\r\nNotes\r\n\r\nShould show off items at some point\r\n\r\n{Twitter Banner}\r\n\r\nFollow us on Twitter to get updates on the game's development!\r\n\r\n{Discord Banner}\r\n\r\nFollow us on Discord to chat with the game's developers and community!\r\n\r\n{Instagram Banner}\r\n\r\nFollow us on Instagram to keep up with our game's art!\r\n```\r\n\r\n#### Source 15\r\n```text\r\nii. Unlike Mario Party, which doesn't exactly have to\r\n                    show off character personalities or why they want to\r\n                    be the superstar because their world is already\r\n                    established, Top Dog could establish the world and\r\n                    characters in one motion.\r\n\r\n                iii. Some current theorized maps, such as the beach map,\r\n                     could be turned into character maps, such as the\r\n                     shark character having his map.\r\n\r\n            b.  Cons:\r\n```\r\n\r\n#### Source 16\r\n```text\r\n>\r\n> `UNKNOWN ARTICLE LINK: Minigame Assets`(#minigame-assets)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Minigame Time Estimates:`(#minigame-time-estimates)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Character Assets`(#character-assets)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Character Time Estimates:`(#character-time-estimates)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Shaders`(#shaders)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Shader Time Estimates:`(#shader-time-estimates)\r\n>\r\n> `UNKNOWN ARTICLE LINK: VFX`(#vfx)\r\n>\r\n> `UNKNOWN ARTICLE LINK: VFX Time Estimates:`(#vfx-time-estimates)\r\n>\r\n> `UNKNOWN ARTICLE LINK: UI Assets:`(#ui-assets)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Out of game:`(#out-of-game-1)\r\n>\r\n> `UNKNOWN ARTICLE LINK: In Game:`(#in-game-1)\r\n>\r\n> `UNKNOWN ARTICLE LINK: UI Asset Time Estimates:`(#ui-asset-time-estimates)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Workshop Assets:`(#workshop-assets)\r\n>\r\n> [[Workshop Template Time\r\n```\r\n\r\n#### Source 17\r\n```text\r\nThis is a spreadsheet for all of our items.\r\n\r\n### Zoom meeting discussing items \r\n\r\n\\\"Item Meeting 8_26_2022.mp4\\\"\r\n\r\n## Characters \r\n\r\n### Playable Character Art \r\n\r\nThese are art assets for the following characters:\r\n\r\nDoug\r\n\r\nFox\r\n\r\nFinn\r\n\r\nDraco\r\n\r\nDoug\r\n\r\nDallas\r\n\r\nClyde\r\n\r\nCatherine\r\n\r\nBonnie\r\n\r\nAntony\r\n\r\n\\\"ClubClubLineupRevise.png\\\" is all the characters in a row\r\n\r\n### NPC Art \r\n\r\nOtis.PNG\r\n\r\nThis is a frog in Enchanted Forest\r\n\r\nFrog.png\r\n\r\nWitch.png\r\n\r\n\\\"Tree Critter\\\".png\r\n\r\nSpacestation_NPC_concept.png\r\n\r\nShopkeeper_owl.png\r\n\r\nShopkeeper_badger.png\r\n\r\nShopkeep_chameleon.png\r\n\r\nShopkeep_chameleon_blank.,png\r\n```\r\n\r\n#### Source 18\r\n```text\r\n1.  Game shows naturally need to show what the characters stand\r\n            to win, and any good game show will get you invested in the\r\n            characters so you care if they win. Additionally, for a new\r\n            game IP, I feel that it is important for us to establish who\r\n            these characters are, where they live in their world, why\r\n            they want to compete in the game show, etc. Frankly, I think\r\n            that just saying the characters want to be the \"Top Dog\"\r\n            doesn't really show the personality we gave them.\r\n```\r\n\r\n#### Source 19\r\n```text\r\n\\- Quickdraw duel\r\n\r\n\\- 2D platformer\r\n\r\n\\- Asteroid shooter\r\n\r\n\\- Squid game parody\r\n\r\n\\- Falling platforms\r\n\r\n\\- Will support single player, local co-op, and online\r\n\r\n\\## Characters\r\n\r\n\\- Each player selects from a number of characters before starting\r\n\r\n\\- Characters have different attributes affecting dice rolls\r\n\r\n\\- Players can customize characters via outfits, colors, accessories\r\n\r\n\\- Abilities planned:\r\n\r\n\\- Double dice roll\r\n\r\n\\- Double mini-game rewards\r\n\r\n\\- Immunity from traps\r\n\r\n\\- Free items\r\n\r\n\\## Items\r\n\r\n\\- Players collect items by purchasing at shops or winning mini-games\r\n```\r\n\r\n#### Source 20\r\n```text\r\n>\r\n> `UNKNOWN ARTICLE LINK: Workshop Assets:`(#workshop-assets)\r\n>\r\n> [[Workshop Template Time\r\n> Estimate:]](#workshop-template-time-estimate)\r\n>\r\n> `UNKNOWN ARTICLE LINK: Animation:`(#animation)\r\n>\r\n> [[Animation Time Estimates [Total: 17-24\r\n> weeks]]](#animation-time-estimates)\r\n```"
};

export default character_specific_animations;