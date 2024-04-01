
const battle_pong = {
	"slug": "Battle Pong",
	"content": "Battle Pong is a minigame in Top Dog where players control paddles to score against one another in a four-player competitive match.\n\n## Gameplay Mechanics\n- Players take control of paddles, reflecting the pong ball to score in opponents' goals.\n- Upon hitting the ball, it changes color indicating the last player to touch it; if this ball scores, the last player to hit it receives a point.\n- Each ball hit slightly increases its speed.\n- Points accumulate for each goal scored against an opponent. \n\n## Developmental Aspects\n\nThe goal was to build upon the classic Pong experience, ensuring engaging and dynamic multiplayer action. During development, balancing the game to discourage targeting specific players to prevent predictability was a key consideration.\n\n`GAME FILE LINK: concept_image_battle_pong.png`\n\n## Relevant Files/Folders\n\n- \"`GAME FILE LINK: design/minigames/battle-pong-doc.md`\"\n- \"`GAME FILE LINK: assets/minigames/battle-pong/`\"\n\n## See Also\n\n- [[Characters]]\n- [[Game Modes]]\n\n## Developer Notes\n\nBrainstorming sessions included ideas for enhancing gameplay, such as introducing different variations of the pong ball to maintain a dynamic play environment.\n\n## Cited Document Text Segments\n\n#### Source 1\n```text\nBattle Pong: Battle Pong (Name WIP)\n\nSimilar to this Pokemon Stadium game: https://youtu.be/9mz-WmzgZyo\n\nSimilar to pong, but with 4 players that are trying to score goals on\none another.\n\nPlayers take control of their respective \"paddles\" that can have some\nsort of angle/mechanic that allows them to aim where the ball goes. Once\na ball is hit by a player, that ball changes color and, if scored in\nanother player's goal, the player who hit it last receives a point.\n\nEach time a ball is hit, the speed slightly increases, so it becomes\nharder to keep in play.\n```\n\n#### Source 2\n```text\nShell Game:\n\n-   elimination shell game where if you pick the cup that has the ball\n    you get knocked out of the game it\\'s partially based on reflex,\n    since two players can\\'t select the same cup, so whoever picks it\n    first gets it\n\nCounting Game:\n\n-   Counting a number of animals/objects in a complex scene, making the\n    winner accuracy based\n\nSpot the Difference:\n\n-   A spot the difference game (winner is whoever finds the most\n    differences)\n\nBattle Pong: Battle Pong (Name WIP)\n\nSimilar to this Pokemon Stadium game: https://youtu.be/9mz-WmzgZyo\n```\n\n#### Source 3\n```text\nLittle Wars:\n\n-   Little Wars\n\n    -   Each player gets a variety of troops to select from then deploys\n        them on the battlefield.\n\n    -   Free for All\n\n    -   Here was an image showing the 4 players each placed on their own\n        island. Bridges connect each island over rivers. Players can\n        select 1 of 4 buttons to deploy a type of troop.\n\nClub Club (jousting):\n\n-   Club Club\n\n    -   Players stand on a beam (battle beam) and take part in a joust.\n\n    -   Players attempt to knock the enemy off the battle beam and into\n        the ball pit without hurting their teammate.\n```\n\n#### Source 4\n```text\n3v1 Battle Minigame\n\n-   3s put up 20 coins each and 1 puts up 60\n\nCoin communism\n\nLiquidate Assets\n\n-   Stars converted to coin value\n\n-   Items converted to coin value\n\nGet the horns\n\n-   A single player mashing minigame\n\nGot your Goat\n\n-   Bowser revolution\n\nHoof it\n\n-   Chase the player back to start\n\n-   Chase the player away from the star\n\nYou've goat mail\n\n-   Send a letter to someone that does [something]{.mark}\n\nAdd spaces in front of player\n\n-   Higher risker and higher reward chance time\n\nAudience throws items @ players\n\n## Link to Figma\n```\n\n#### Source 5\n```text\nBandstand:\n\n-   Better Mario Party Bandstand\n\n    -   Heavy inspiration from [[this\n        game]](https://www.youtube.com/watch?v=aOCTCSh-JwA),\n        except we don\\'t make it for babies.\n\n    -   Notes don\\'t fall on the down beat of the music, so it\\'s harder\n        to get the rhythm correct.\n\n    -   The song gets faster as time goes on.\n\n    -   No conductor role at all. Just a bunch of guys playing\n        instruments.\n\nHyper Laser Tag:\n\n-   Hyper Laser Tag\n\n    -   Top-down battle free-for-all on a stage with hazards.\n```\n\n#### Source 6\n```text\nHyper Laser Tag:\n\n-   Hyper Laser Tag\n\n    -   Top-down battle free-for-all on a stage with hazards.\n\n    -   Players can move, shoot in a chosen direction, roll in a chosen\n        direction, and very briefly reflect shots that would hit them.\n\n    -   There is a cooldown for each of these actions. A player should\n        be able to shoot more often than they can reflect or evade.\n\n    -   Players have a number of times they can be hit before they are\n        removed from play.\n```\n\n#### Source 7\n```text\n-   Players have a number of times they can be hit before they are\n        removed from play.\n\n    -   As play progresses, the state of the stage changes and\n        introduces hazards, e.g. a node that emits an expanding circle\n        that MUST be rolled through, or sections that pop up that also\n        reflect shots.\n\nTesla Rhythm:\n\nTesla Rhythm\n\n-   Free-for-all survival with battle elements and a rhythmic twist.\n\n-   Bolts of electricity streak across the stream in time with the\n    music, an indicator on the floor shows where and when the bolt will\n    strike.\n```\n\n#### Source 8\n```text\n-   Waiting to join/ queue menu\n\n    -   Join code generation/input menu to invite people via codes\n\n-   Workshop content menu (enable/disable/view mods)\n\n-   Battle Pass/Quest Menu\n\n    -   Cosmetic menu, to switch between cosmetics\n\n-   Map selection menu\n\n    -   Possible map settings menu (deciding what is enabled/disabled\n        for a game)\n\n    -   Character select menu\n\n-   Game summary screen, with game performance metrics\n\n-   Achievement progress menu [OPTIONAL]\n\n##### In Game: \n\n-   Dialogue Boxes with choices\n\n-   Shop menu\n```\n\n#### Source 9\n```text\nConcept Image that shows 4 players each controlling a paddle to hit the\nball with.\n\nPossible Idea extensions\n\nMaybe have two ball variations, a big ball that moves slower worth 2\npoints and a regular 1 point ball? Maybe just a variation of the regular\nball but it's golden (like how mario party does) and worth more points\n\nMoving platforms that can block balls to mix up play?\n\nAs far as art, we could incorporate the players moving the paddles or it\ncould look similar to a neon version of pong. Visuals could be simple in\nthat case\n\nPossible Problems\n```\n\n#### Source 10\n```text\n-   Load Screen\n\n-   Multiplayer menu (with options for different modes)\n\n    -   Waiting to join/ queue menu\n\n    -   Join code generation/input menu to invite people via codes\n\n-   Workshop content menu (enable/disable/view mods)\n\n-   Battle Pass/Quest Menu\n\n    -   Cosmetic menu, to switch between cosmetics\n\n-   Map selection menu\n\n    -   Possible map settings menu (deciding what is enabled/disabled\n        for a game)\n\n    -   Character select menu\n\n-   Game summary screen, with game performance metrics\n\n-   Achievement progress menu [OPTIONAL]\n\n##### In Game:\n```\n\n#### Source 11\n```text\n-   Could target players trap spaces and turn them into Phil traps\n        (not phil spaces) that have negative effects.\n\n-   Next golden bone costs double.\n\n-   Lost half your stars (late game possibly), maybe scales as a fixed\n    amount\n\n-   Next movement, player stops and trigger the next trap space they\n    walk over\n\n-   If a player has 0 coins, they get x coins\n\nGriffin Games\\\nTop Dog: Phil Space Actions\n\nMinigame to steal coins\n\n-   3v1 where either 3 get to steal coins from 1\n\n3v1 Battle Minigame\n\n-   3s put up 20 coins each and 1 puts up 60\n\nCoin communism\n\nLiquidate Assets\n```"
};

export default battle_pong;