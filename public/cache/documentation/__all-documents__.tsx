
import game_content from "./Game Content/__export__";
import naive_bayes_classifier from "./naive_bayes_classifier"; //MD IDENTIFIED
import overview from "./Overview/__export__";


const allDocs = {
	"game_content": game_content,
	"naive_bayes_classifier": naive_bayes_classifier,
	"overview": overview
};

export default allDocs;


export const folder_structure = {
	"Game Content": {
		"Boards": {
			"Board Events and Gimmicks": null,
			"General Board Features": null,
			"Theme-Specific Boards": {
				"Enchanted Forest Board": null,
				"Space Station Board": null,
				"Wetworld Board": null
			}
		},
		"Characters": {
			"Non-Playable Characters": {
				"Critters": null,
				"Host Character": null,
				"Shopkeepers": null,
				"Villain Characters": null
			},
			"Playable Characters": {
				"Antony": null,
				"Bonnie": null,
				"Catherine": null,
				"Clyde": null,
				"Dallas": null,
				"Doug": null,
				"Draco": null,
				"Finn": null,
				"Paulie": null,
				"Renard": null
			}
		},
		"Community & Workshop": {
			"Steam Workshop Integration": null,
			"Workshop Asset Templates": null
		},
		"Critters": {
			"Board Specific Critters": {
				"Enchanted Forest Critters": null,
				"Space Station Critters": null,
				"Wetworld Critters": null
			},
			"Generic Creatures Role and Behavior": null
		},
		"Development Process": {
			"Art & Design": {
				"Character and Map Asset Creation": null,
				"General Art Process": null,
				"Shader and Texture Libraries": null
			},
			"Planning & Management": {
				"Documentation and Meetings": null,
				"Kickstarter Campaign Materials": {
					"Drafts and Feedback": null,
					"Trailer Content Checklists": null
				}
			},
			"Programming & Coding": {
				"Board Logic": null,
				"Mini-Game Logic": null,
				"Networking or Multiplayer": null,
				"Workshop Support": null
			},
			"Testing & Quality Assurance": {
				"Balance and Gameplay Adjustments": null,
				"Community Feedback Mechanisms": null,
				"Internal Playtesting": null
			}
		},
		"Executive's Corner": {
			"Challenges": null,
			"Financial Goals and Timeline": null,
			"Kickstarter Planning": null
		},
		"Game Modes": {
			"Board Only": null,
			"Classic": null,
			"Competitive And Casual Playlists": null,
			"Infinite Play": null,
			"Mini Games Only": null
		},
		"Items & Power-Ups": {
			"Character Specific Items": {
				"Catherine Gamer Rage": null,
				"Clyde Traps": null,
				"Doug Buried Bone Map": null,
				"Paulie Plane Ticket": null
			},
			"Enchanted Forest Items": {
				"Call Of The Forest": null,
				"Grape Vine": null,
				"Mystery Mushroom": null,
				"Pinwheel": null,
				"Reap And Sow": null,
				"Stun Spore Hat": null
			},
			"Universal Items": {
				"AOE Delayed Trap": null,
				"Banana Peel": null,
				"Battal Buzzer": null,
				"Bounce Off": null,
				"Break The Bank": null,
				"Curse Roll": null,
				"Declaration Die": null,
				"Double Up Tennis Ball": null,
				"Flip Flop": null,
				"Game Chooser": null,
				"Game Gambler": null,
				"Golden Mic": null,
				"Growth Item": null,
				"Item Stealing": null,
				"Lavender": null,
				"Pants On Fire": null,
				"Phil Bomb": null,
				"Piggy Bank": null,
				"Polarity Inverter": null,
				"Quick Spender": null,
				"Reverse Mushroom": null,
				"Roll Booster": null,
				"Shop Ticket": null,
				"Star Ticket": null,
				"Teleporter": null,
				"Trap Card Trap": null,
				"Trap Protection": null,
				"Trap Square Random Warp": null,
				"Triple Up Tennis Ball": null,
				"Unique Duplicate": null,
				"Wet Fish": null,
				"Wish Bone": null
			}
		},
		"Marketing and Community": {
			"Content Examples": null,
			"Social Media Platforms": null,
			"Social Media Strategy": null
		},
		"Mini-Games": {
			"Action Games": {
				"Attack on Ganymede": null,
				"Club Club": null,
				"Hyper Laser Tag": null,
				"Quickdraw": null
			},
			"Luck-Based Games": {
				"Counting Game": null,
				"Shell Game": null,
				"Spot the Difference": null
			},
			"Strategy Games": {
				"Little Wars": null,
				"Marauders of the Missing Macguffin": null
			},
			"Uncategorized Games": {
				"Bandstand": null,
				"Battle Pong": null,
				"Failing Upwards": null,
				"Seconds Before Disaster": null,
				"Squid Games": null,
				"Unhandy Dandies": null,
				"Water Striders": null
			}
		},
		"Resources & Assets": {
			"Art & Animation": {
				"Animation Libraries": {
					"Character Specific Animations": null,
					"Universal Animations": null
				},
				"Board and Environment Art": null,
				"Character Art and Icons": null,
				"Logos": {
					"Griffin Games Logos": null,
					"Top Dog Game Logos": null
				}
			},
			"Marketing Materials": {
				"Promotional Art": null,
				"Social Media Assets": null,
				"Trailers": null
			},
			"Music & Audio": {
				"Music Themes and Files": null,
				"Sound Effects and VFX": null
			},
			"Prototypes & Concepts": {
				"Concept Art and Sketches": null,
				"Prototype Videos": null,
				"UI Designs and Prototypes": null
			}
		}
	},
	"Naive Bayes Classifier": null,
	"Overview": {
		"Introduction to Top Dog": null
	}
};

export const reverse_lookup = {
	"overview/introduction_to_top_dog": [
		"Overview",
		"Introduction to Top Dog"
	],
	"game_content/resources_assets/prototypes_concepts/concept_art_and_sketches": [
		"Game Content",
		"Resources & Assets",
		"Prototypes & Concepts",
		"Concept Art and Sketches"
	],
	"game_content/resources_assets/prototypes_concepts/prototype_videos": [
		"Game Content",
		"Resources & Assets",
		"Prototypes & Concepts",
		"Prototype Videos"
	],
	"game_content/resources_assets/prototypes_concepts/ui_designs_and_prototypes": [
		"Game Content",
		"Resources & Assets",
		"Prototypes & Concepts",
		"UI Designs and Prototypes"
	],
	"game_content/resources_assets/music_audio/music_themes_and_files": [
		"Game Content",
		"Resources & Assets",
		"Music & Audio",
		"Music Themes and Files"
	],
	"game_content/resources_assets/music_audio/sound_effects_and_vfx": [
		"Game Content",
		"Resources & Assets",
		"Music & Audio",
		"Sound Effects and VFX"
	],
	"game_content/resources_assets/marketing_materials/promotional_art": [
		"Game Content",
		"Resources & Assets",
		"Marketing Materials",
		"Promotional Art"
	],
	"game_content/resources_assets/marketing_materials/social_media_assets": [
		"Game Content",
		"Resources & Assets",
		"Marketing Materials",
		"Social Media Assets"
	],
	"game_content/resources_assets/marketing_materials/trailers": [
		"Game Content",
		"Resources & Assets",
		"Marketing Materials",
		"Trailers"
	],
	"game_content/resources_assets/art_animation/logos/griffin_games_logos": [
		"Game Content",
		"Resources & Assets",
		"Art & Animation",
		"Logos",
		"Griffin Games Logos"
	],
	"game_content/resources_assets/art_animation/logos/top_dog_game_logos": [
		"Game Content",
		"Resources & Assets",
		"Art & Animation",
		"Logos",
		"Top Dog Game Logos"
	],
	"game_content/resources_assets/art_animation/animation_libraries/character_specific_animations": [
		"Game Content",
		"Resources & Assets",
		"Art & Animation",
		"Animation Libraries",
		"Character Specific Animations"
	],
	"game_content/resources_assets/art_animation/animation_libraries/universal_animations": [
		"Game Content",
		"Resources & Assets",
		"Art & Animation",
		"Animation Libraries",
		"Universal Animations"
	],
	"game_content/resources_assets/art_animation/board_and_environment_art": [
		"Game Content",
		"Resources & Assets",
		"Art & Animation",
		"Board and Environment Art"
	],
	"game_content/resources_assets/art_animation/character_art_and_icons": [
		"Game Content",
		"Resources & Assets",
		"Art & Animation",
		"Character Art and Icons"
	],
	"game_content/minigames/uncategorized_games/bandstand": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Bandstand"
	],
	"game_content/minigames/uncategorized_games/battle_pong": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Battle Pong"
	],
	"game_content/minigames/uncategorized_games/failing_upwards": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Failing Upwards"
	],
	"game_content/minigames/uncategorized_games/seconds_before_disaster": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Seconds Before Disaster"
	],
	"game_content/minigames/uncategorized_games/squid_games": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Squid Games"
	],
	"game_content/minigames/uncategorized_games/unhandy_dandies": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Unhandy Dandies"
	],
	"game_content/minigames/uncategorized_games/water_striders": [
		"Game Content",
		"Mini-Games",
		"Uncategorized Games",
		"Water Striders"
	],
	"game_content/minigames/strategy_games/little_wars": [
		"Game Content",
		"Mini-Games",
		"Strategy Games",
		"Little Wars"
	],
	"game_content/minigames/strategy_games/marauders_of_the_missing_macguffin": [
		"Game Content",
		"Mini-Games",
		"Strategy Games",
		"Marauders of the Missing Macguffin"
	],
	"game_content/minigames/luckbased_games/counting_game": [
		"Game Content",
		"Mini-Games",
		"Luck-Based Games",
		"Counting Game"
	],
	"game_content/minigames/luckbased_games/shell_game": [
		"Game Content",
		"Mini-Games",
		"Luck-Based Games",
		"Shell Game"
	],
	"game_content/minigames/luckbased_games/spot_the_difference": [
		"Game Content",
		"Mini-Games",
		"Luck-Based Games",
		"Spot the Difference"
	],
	"game_content/minigames/action_games/attack_on_ganymede": [
		"Game Content",
		"Mini-Games",
		"Action Games",
		"Attack on Ganymede"
	],
	"game_content/minigames/action_games/club_club": [
		"Game Content",
		"Mini-Games",
		"Action Games",
		"Club Club"
	],
	"game_content/minigames/action_games/hyper_laser_tag": [
		"Game Content",
		"Mini-Games",
		"Action Games",
		"Hyper Laser Tag"
	],
	"game_content/minigames/action_games/quickdraw": [
		"Game Content",
		"Mini-Games",
		"Action Games",
		"Quickdraw"
	],
	"game_content/marketing_and_community/content_examples": [
		"Game Content",
		"Marketing and Community",
		"Content Examples"
	],
	"game_content/marketing_and_community/social_media_platforms": [
		"Game Content",
		"Marketing and Community",
		"Social Media Platforms"
	],
	"game_content/marketing_and_community/social_media_strategy": [
		"Game Content",
		"Marketing and Community",
		"Social Media Strategy"
	],
	"game_content/items_powerups/universal_items/aoe_delayed_trap": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"AOE Delayed Trap"
	],
	"game_content/items_powerups/universal_items/banana_peel": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Banana Peel"
	],
	"game_content/items_powerups/universal_items/battal_buzzer": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Battal Buzzer"
	],
	"game_content/items_powerups/universal_items/bounce_off": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Bounce Off"
	],
	"game_content/items_powerups/universal_items/break_the_bank": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Break The Bank"
	],
	"game_content/items_powerups/universal_items/curse_roll": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Curse Roll"
	],
	"game_content/items_powerups/universal_items/declaration_die": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Declaration Die"
	],
	"game_content/items_powerups/universal_items/double_up_tennis_ball": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Double Up Tennis Ball"
	],
	"game_content/items_powerups/universal_items/flip_flop": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Flip Flop"
	],
	"game_content/items_powerups/universal_items/game_chooser": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Game Chooser"
	],
	"game_content/items_powerups/universal_items/game_gambler": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Game Gambler"
	],
	"game_content/items_powerups/universal_items/golden_mic": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Golden Mic"
	],
	"game_content/items_powerups/universal_items/growth_item": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Growth Item"
	],
	"game_content/items_powerups/universal_items/item_stealing": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Item Stealing"
	],
	"game_content/items_powerups/universal_items/lavender": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Lavender"
	],
	"game_content/items_powerups/universal_items/pants_on_fire": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Pants On Fire"
	],
	"game_content/items_powerups/universal_items/phil_bomb": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Phil Bomb"
	],
	"game_content/items_powerups/universal_items/piggy_bank": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Piggy Bank"
	],
	"game_content/items_powerups/universal_items/polarity_inverter": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Polarity Inverter"
	],
	"game_content/items_powerups/universal_items/quick_spender": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Quick Spender"
	],
	"game_content/items_powerups/universal_items/reverse_mushroom": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Reverse Mushroom"
	],
	"game_content/items_powerups/universal_items/roll_booster": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Roll Booster"
	],
	"game_content/items_powerups/universal_items/shop_ticket": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Shop Ticket"
	],
	"game_content/items_powerups/universal_items/star_ticket": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Star Ticket"
	],
	"game_content/items_powerups/universal_items/teleporter": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Teleporter"
	],
	"game_content/items_powerups/universal_items/trap_card_trap": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Trap Card Trap"
	],
	"game_content/items_powerups/universal_items/trap_protection": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Trap Protection"
	],
	"game_content/items_powerups/universal_items/trap_square_random_warp": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Trap Square Random Warp"
	],
	"game_content/items_powerups/universal_items/triple_up_tennis_ball": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Triple Up Tennis Ball"
	],
	"game_content/items_powerups/universal_items/unique_duplicate": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Unique Duplicate"
	],
	"game_content/items_powerups/universal_items/wet_fish": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Wet Fish"
	],
	"game_content/items_powerups/universal_items/wish_bone": [
		"Game Content",
		"Items & Power-Ups",
		"Universal Items",
		"Wish Bone"
	],
	"game_content/items_powerups/enchanted_forest_items/call_of_the_forest": [
		"Game Content",
		"Items & Power-Ups",
		"Enchanted Forest Items",
		"Call Of The Forest"
	],
	"game_content/items_powerups/enchanted_forest_items/grape_vine": [
		"Game Content",
		"Items & Power-Ups",
		"Enchanted Forest Items",
		"Grape Vine"
	],
	"game_content/items_powerups/enchanted_forest_items/mystery_mushroom": [
		"Game Content",
		"Items & Power-Ups",
		"Enchanted Forest Items",
		"Mystery Mushroom"
	],
	"game_content/items_powerups/enchanted_forest_items/pinwheel": [
		"Game Content",
		"Items & Power-Ups",
		"Enchanted Forest Items",
		"Pinwheel"
	],
	"game_content/items_powerups/enchanted_forest_items/reap_and_sow": [
		"Game Content",
		"Items & Power-Ups",
		"Enchanted Forest Items",
		"Reap And Sow"
	],
	"game_content/items_powerups/enchanted_forest_items/stun_spore_hat": [
		"Game Content",
		"Items & Power-Ups",
		"Enchanted Forest Items",
		"Stun Spore Hat"
	],
	"game_content/items_powerups/character_specific_items/catherine_gamer_rage": [
		"Game Content",
		"Items & Power-Ups",
		"Character Specific Items",
		"Catherine Gamer Rage"
	],
	"game_content/items_powerups/character_specific_items/clyde_traps": [
		"Game Content",
		"Items & Power-Ups",
		"Character Specific Items",
		"Clyde Traps"
	],
	"game_content/items_powerups/character_specific_items/doug_buried_bone_map": [
		"Game Content",
		"Items & Power-Ups",
		"Character Specific Items",
		"Doug Buried Bone Map"
	],
	"game_content/items_powerups/character_specific_items/paulie_plane_ticket": [
		"Game Content",
		"Items & Power-Ups",
		"Character Specific Items",
		"Paulie Plane Ticket"
	],
	"game_content/game_modes/board_only": [
		"Game Content",
		"Game Modes",
		"Board Only"
	],
	"game_content/game_modes/classic": [
		"Game Content",
		"Game Modes",
		"Classic"
	],
	"game_content/game_modes/competitive_and_casual_playlists": [
		"Game Content",
		"Game Modes",
		"Competitive And Casual Playlists"
	],
	"game_content/game_modes/infinite_play": [
		"Game Content",
		"Game Modes",
		"Infinite Play"
	],
	"game_content/game_modes/mini_games_only": [
		"Game Content",
		"Game Modes",
		"Mini Games Only"
	],
	"game_content/executives_corner/challenges": [
		"Game Content",
		"Executive's Corner",
		"Challenges"
	],
	"game_content/executives_corner/financial_goals_and_timeline": [
		"Game Content",
		"Executive's Corner",
		"Financial Goals and Timeline"
	],
	"game_content/executives_corner/kickstarter_planning": [
		"Game Content",
		"Executive's Corner",
		"Kickstarter Planning"
	],
	"game_content/development_process/testing_quality_assurance/balance_and_gameplay_adjustments": [
		"Game Content",
		"Development Process",
		"Testing & Quality Assurance",
		"Balance and Gameplay Adjustments"
	],
	"game_content/development_process/testing_quality_assurance/community_feedback_mechanisms": [
		"Game Content",
		"Development Process",
		"Testing & Quality Assurance",
		"Community Feedback Mechanisms"
	],
	"game_content/development_process/testing_quality_assurance/internal_playtesting": [
		"Game Content",
		"Development Process",
		"Testing & Quality Assurance",
		"Internal Playtesting"
	],
	"game_content/development_process/programming_coding/board_logic": [
		"Game Content",
		"Development Process",
		"Programming & Coding",
		"Board Logic"
	],
	"game_content/development_process/programming_coding/minigame_logic": [
		"Game Content",
		"Development Process",
		"Programming & Coding",
		"Mini-Game Logic"
	],
	"game_content/development_process/programming_coding/networking_or_multiplayer": [
		"Game Content",
		"Development Process",
		"Programming & Coding",
		"Networking or Multiplayer"
	],
	"game_content/development_process/programming_coding/workshop_support": [
		"Game Content",
		"Development Process",
		"Programming & Coding",
		"Workshop Support"
	],
	"game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback": [
		"Game Content",
		"Development Process",
		"Planning & Management",
		"Kickstarter Campaign Materials",
		"Drafts and Feedback"
	],
	"game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists": [
		"Game Content",
		"Development Process",
		"Planning & Management",
		"Kickstarter Campaign Materials",
		"Trailer Content Checklists"
	],
	"game_content/development_process/planning_management/documentation_and_meetings": [
		"Game Content",
		"Development Process",
		"Planning & Management",
		"Documentation and Meetings"
	],
	"game_content/development_process/art_design/character_and_map_asset_creation": [
		"Game Content",
		"Development Process",
		"Art & Design",
		"Character and Map Asset Creation"
	],
	"game_content/development_process/art_design/general_art_process": [
		"Game Content",
		"Development Process",
		"Art & Design",
		"General Art Process"
	],
	"game_content/development_process/art_design/shader_and_texture_libraries": [
		"Game Content",
		"Development Process",
		"Art & Design",
		"Shader and Texture Libraries"
	],
	"game_content/critters/board_specific_critters/enchanted_forest_critters": [
		"Game Content",
		"Critters",
		"Board Specific Critters",
		"Enchanted Forest Critters"
	],
	"game_content/critters/board_specific_critters/space_station_critters": [
		"Game Content",
		"Critters",
		"Board Specific Critters",
		"Space Station Critters"
	],
	"game_content/critters/board_specific_critters/wetworld_critters": [
		"Game Content",
		"Critters",
		"Board Specific Critters",
		"Wetworld Critters"
	],
	"game_content/critters/generic_creatures_role_and_behavior": [
		"Game Content",
		"Critters",
		"Generic Creatures Role and Behavior"
	],
	"game_content/community_workshop/steam_workshop_integration": [
		"Game Content",
		"Community & Workshop",
		"Steam Workshop Integration"
	],
	"game_content/community_workshop/workshop_asset_templates": [
		"Game Content",
		"Community & Workshop",
		"Workshop Asset Templates"
	],
	"game_content/characters/playable_characters/antony": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Antony"
	],
	"game_content/characters/playable_characters/bonnie": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Bonnie"
	],
	"game_content/characters/playable_characters/catherine": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Catherine"
	],
	"game_content/characters/playable_characters/clyde": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Clyde"
	],
	"game_content/characters/playable_characters/dallas": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Dallas"
	],
	"game_content/characters/playable_characters/doug": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Doug"
	],
	"game_content/characters/playable_characters/draco": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Draco"
	],
	"game_content/characters/playable_characters/finn": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Finn"
	],
	"game_content/characters/playable_characters/paulie": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Paulie"
	],
	"game_content/characters/playable_characters/renard": [
		"Game Content",
		"Characters",
		"Playable Characters",
		"Renard"
	],
	"game_content/characters/nonplayable_characters/critters": [
		"Game Content",
		"Characters",
		"Non-Playable Characters",
		"Critters"
	],
	"game_content/characters/nonplayable_characters/host_character": [
		"Game Content",
		"Characters",
		"Non-Playable Characters",
		"Host Character"
	],
	"game_content/characters/nonplayable_characters/shopkeepers": [
		"Game Content",
		"Characters",
		"Non-Playable Characters",
		"Shopkeepers"
	],
	"game_content/characters/nonplayable_characters/villain_characters": [
		"Game Content",
		"Characters",
		"Non-Playable Characters",
		"Villain Characters"
	],
	"game_content/boards/themespecific_boards/enchanted_forest_board": [
		"Game Content",
		"Boards",
		"Theme-Specific Boards",
		"Enchanted Forest Board"
	],
	"game_content/boards/themespecific_boards/space_station_board": [
		"Game Content",
		"Boards",
		"Theme-Specific Boards",
		"Space Station Board"
	],
	"game_content/boards/themespecific_boards/wetworld_board": [
		"Game Content",
		"Boards",
		"Theme-Specific Boards",
		"Wetworld Board"
	],
	"game_content/boards/board_events_and_gimmicks": [
		"Game Content",
		"Boards",
		"Board Events and Gimmicks"
	],
	"game_content/boards/general_board_features": [
		"Game Content",
		"Boards",
		"General Board Features"
	],
	"naive_bayes_classifier": [
		"Naive Bayes Classifier"
	]
};

export const folder_structure_aliases = {
	"documentation/Overview/Introduction to Top Dog": "overview/introduction_to_top_dog",
	"Overview/Introduction to Top Dog": "overview/introduction_to_top_dog",
	"Introduction to Top Dog": "overview/introduction_to_top_dog",
	"documentation/Game Content/Resources & Assets/Prototypes & Concepts/Concept Art and Sketches": "game_content/resources_assets/prototypes_concepts/concept_art_and_sketches",
	"Game Content/Resources & Assets/Prototypes & Concepts/Concept Art and Sketches": "game_content/resources_assets/prototypes_concepts/concept_art_and_sketches",
	"Resources & Assets/Prototypes & Concepts/Concept Art and Sketches": "game_content/resources_assets/prototypes_concepts/concept_art_and_sketches",
	"Prototypes & Concepts/Concept Art and Sketches": "game_content/resources_assets/prototypes_concepts/concept_art_and_sketches",
	"Concept Art and Sketches": "game_content/resources_assets/prototypes_concepts/concept_art_and_sketches",
	"documentation/Game Content/Resources & Assets/Prototypes & Concepts/Prototype Videos": "game_content/resources_assets/prototypes_concepts/prototype_videos",
	"Game Content/Resources & Assets/Prototypes & Concepts/Prototype Videos": "game_content/resources_assets/prototypes_concepts/prototype_videos",
	"Resources & Assets/Prototypes & Concepts/Prototype Videos": "game_content/resources_assets/prototypes_concepts/prototype_videos",
	"Prototypes & Concepts/Prototype Videos": "game_content/resources_assets/prototypes_concepts/prototype_videos",
	"Prototype Videos": "game_content/resources_assets/prototypes_concepts/prototype_videos",
	"documentation/Game Content/Resources & Assets/Prototypes & Concepts/UI Designs and Prototypes": "game_content/resources_assets/prototypes_concepts/ui_designs_and_prototypes",
	"Game Content/Resources & Assets/Prototypes & Concepts/UI Designs and Prototypes": "game_content/resources_assets/prototypes_concepts/ui_designs_and_prototypes",
	"Resources & Assets/Prototypes & Concepts/UI Designs and Prototypes": "game_content/resources_assets/prototypes_concepts/ui_designs_and_prototypes",
	"Prototypes & Concepts/UI Designs and Prototypes": "game_content/resources_assets/prototypes_concepts/ui_designs_and_prototypes",
	"UI Designs and Prototypes": "game_content/resources_assets/prototypes_concepts/ui_designs_and_prototypes",
	"documentation/Game Content/Resources & Assets/Music & Audio/Music Themes and Files": "game_content/resources_assets/music_audio/music_themes_and_files",
	"Game Content/Resources & Assets/Music & Audio/Music Themes and Files": "game_content/resources_assets/music_audio/music_themes_and_files",
	"Resources & Assets/Music & Audio/Music Themes and Files": "game_content/resources_assets/music_audio/music_themes_and_files",
	"Music & Audio/Music Themes and Files": "game_content/resources_assets/music_audio/music_themes_and_files",
	"Music Themes and Files": "game_content/resources_assets/music_audio/music_themes_and_files",
	"documentation/Game Content/Resources & Assets/Music & Audio/Sound Effects and VFX": "game_content/resources_assets/music_audio/sound_effects_and_vfx",
	"Game Content/Resources & Assets/Music & Audio/Sound Effects and VFX": "game_content/resources_assets/music_audio/sound_effects_and_vfx",
	"Resources & Assets/Music & Audio/Sound Effects and VFX": "game_content/resources_assets/music_audio/sound_effects_and_vfx",
	"Music & Audio/Sound Effects and VFX": "game_content/resources_assets/music_audio/sound_effects_and_vfx",
	"Sound Effects and VFX": "game_content/resources_assets/music_audio/sound_effects_and_vfx",
	"documentation/Game Content/Resources & Assets/Marketing Materials/Promotional Art": "game_content/resources_assets/marketing_materials/promotional_art",
	"Game Content/Resources & Assets/Marketing Materials/Promotional Art": "game_content/resources_assets/marketing_materials/promotional_art",
	"Resources & Assets/Marketing Materials/Promotional Art": "game_content/resources_assets/marketing_materials/promotional_art",
	"Marketing Materials/Promotional Art": "game_content/resources_assets/marketing_materials/promotional_art",
	"Promotional Art": "game_content/resources_assets/marketing_materials/promotional_art",
	"documentation/Game Content/Resources & Assets/Marketing Materials/Social Media Assets": "game_content/resources_assets/marketing_materials/social_media_assets",
	"Game Content/Resources & Assets/Marketing Materials/Social Media Assets": "game_content/resources_assets/marketing_materials/social_media_assets",
	"Resources & Assets/Marketing Materials/Social Media Assets": "game_content/resources_assets/marketing_materials/social_media_assets",
	"Marketing Materials/Social Media Assets": "game_content/resources_assets/marketing_materials/social_media_assets",
	"Social Media Assets": "game_content/resources_assets/marketing_materials/social_media_assets",
	"documentation/Game Content/Resources & Assets/Marketing Materials/Trailers": "game_content/resources_assets/marketing_materials/trailers",
	"Game Content/Resources & Assets/Marketing Materials/Trailers": "game_content/resources_assets/marketing_materials/trailers",
	"Resources & Assets/Marketing Materials/Trailers": "game_content/resources_assets/marketing_materials/trailers",
	"Marketing Materials/Trailers": "game_content/resources_assets/marketing_materials/trailers",
	"Trailers": "game_content/resources_assets/marketing_materials/trailers",
	"documentation/Game Content/Resources & Assets/Art & Animation/Logos/Griffin Games Logos": "game_content/resources_assets/art_animation/logos/griffin_games_logos",
	"Game Content/Resources & Assets/Art & Animation/Logos/Griffin Games Logos": "game_content/resources_assets/art_animation/logos/griffin_games_logos",
	"Resources & Assets/Art & Animation/Logos/Griffin Games Logos": "game_content/resources_assets/art_animation/logos/griffin_games_logos",
	"Art & Animation/Logos/Griffin Games Logos": "game_content/resources_assets/art_animation/logos/griffin_games_logos",
	"Logos/Griffin Games Logos": "game_content/resources_assets/art_animation/logos/griffin_games_logos",
	"Griffin Games Logos": "game_content/resources_assets/art_animation/logos/griffin_games_logos",
	"documentation/Game Content/Resources & Assets/Art & Animation/Logos/Top Dog Game Logos": "game_content/resources_assets/art_animation/logos/top_dog_game_logos",
	"Game Content/Resources & Assets/Art & Animation/Logos/Top Dog Game Logos": "game_content/resources_assets/art_animation/logos/top_dog_game_logos",
	"Resources & Assets/Art & Animation/Logos/Top Dog Game Logos": "game_content/resources_assets/art_animation/logos/top_dog_game_logos",
	"Art & Animation/Logos/Top Dog Game Logos": "game_content/resources_assets/art_animation/logos/top_dog_game_logos",
	"Logos/Top Dog Game Logos": "game_content/resources_assets/art_animation/logos/top_dog_game_logos",
	"Top Dog Game Logos": "game_content/resources_assets/art_animation/logos/top_dog_game_logos",
	"documentation/Game Content/Resources & Assets/Art & Animation/Animation Libraries/Character Specific Animations": "game_content/resources_assets/art_animation/animation_libraries/character_specific_animations",
	"Game Content/Resources & Assets/Art & Animation/Animation Libraries/Character Specific Animations": "game_content/resources_assets/art_animation/animation_libraries/character_specific_animations",
	"Resources & Assets/Art & Animation/Animation Libraries/Character Specific Animations": "game_content/resources_assets/art_animation/animation_libraries/character_specific_animations",
	"Art & Animation/Animation Libraries/Character Specific Animations": "game_content/resources_assets/art_animation/animation_libraries/character_specific_animations",
	"Animation Libraries/Character Specific Animations": "game_content/resources_assets/art_animation/animation_libraries/character_specific_animations",
	"Character Specific Animations": "game_content/resources_assets/art_animation/animation_libraries/character_specific_animations",
	"documentation/Game Content/Resources & Assets/Art & Animation/Animation Libraries/Universal Animations": "game_content/resources_assets/art_animation/animation_libraries/universal_animations",
	"Game Content/Resources & Assets/Art & Animation/Animation Libraries/Universal Animations": "game_content/resources_assets/art_animation/animation_libraries/universal_animations",
	"Resources & Assets/Art & Animation/Animation Libraries/Universal Animations": "game_content/resources_assets/art_animation/animation_libraries/universal_animations",
	"Art & Animation/Animation Libraries/Universal Animations": "game_content/resources_assets/art_animation/animation_libraries/universal_animations",
	"Animation Libraries/Universal Animations": "game_content/resources_assets/art_animation/animation_libraries/universal_animations",
	"Universal Animations": "game_content/resources_assets/art_animation/animation_libraries/universal_animations",
	"documentation/Game Content/Resources & Assets/Art & Animation/Board and Environment Art": "game_content/resources_assets/art_animation/board_and_environment_art",
	"Game Content/Resources & Assets/Art & Animation/Board and Environment Art": "game_content/resources_assets/art_animation/board_and_environment_art",
	"Resources & Assets/Art & Animation/Board and Environment Art": "game_content/resources_assets/art_animation/board_and_environment_art",
	"Art & Animation/Board and Environment Art": "game_content/resources_assets/art_animation/board_and_environment_art",
	"Board and Environment Art": "game_content/resources_assets/art_animation/board_and_environment_art",
	"documentation/Game Content/Resources & Assets/Art & Animation/Character Art and Icons": "game_content/resources_assets/art_animation/character_art_and_icons",
	"Game Content/Resources & Assets/Art & Animation/Character Art and Icons": "game_content/resources_assets/art_animation/character_art_and_icons",
	"Resources & Assets/Art & Animation/Character Art and Icons": "game_content/resources_assets/art_animation/character_art_and_icons",
	"Art & Animation/Character Art and Icons": "game_content/resources_assets/art_animation/character_art_and_icons",
	"Character Art and Icons": "game_content/resources_assets/art_animation/character_art_and_icons",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Bandstand": "game_content/minigames/uncategorized_games/bandstand",
	"Game Content/Mini-Games/Uncategorized Games/Bandstand": "game_content/minigames/uncategorized_games/bandstand",
	"Mini-Games/Uncategorized Games/Bandstand": "game_content/minigames/uncategorized_games/bandstand",
	"Uncategorized Games/Bandstand": "game_content/minigames/uncategorized_games/bandstand",
	"Bandstand": "game_content/minigames/uncategorized_games/bandstand",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Battle Pong": "game_content/minigames/uncategorized_games/battle_pong",
	"Game Content/Mini-Games/Uncategorized Games/Battle Pong": "game_content/minigames/uncategorized_games/battle_pong",
	"Mini-Games/Uncategorized Games/Battle Pong": "game_content/minigames/uncategorized_games/battle_pong",
	"Uncategorized Games/Battle Pong": "game_content/minigames/uncategorized_games/battle_pong",
	"Battle Pong": "game_content/minigames/uncategorized_games/battle_pong",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Failing Upwards": "game_content/minigames/uncategorized_games/failing_upwards",
	"Game Content/Mini-Games/Uncategorized Games/Failing Upwards": "game_content/minigames/uncategorized_games/failing_upwards",
	"Mini-Games/Uncategorized Games/Failing Upwards": "game_content/minigames/uncategorized_games/failing_upwards",
	"Uncategorized Games/Failing Upwards": "game_content/minigames/uncategorized_games/failing_upwards",
	"Failing Upwards": "game_content/minigames/uncategorized_games/failing_upwards",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Seconds Before Disaster": "game_content/minigames/uncategorized_games/seconds_before_disaster",
	"Game Content/Mini-Games/Uncategorized Games/Seconds Before Disaster": "game_content/minigames/uncategorized_games/seconds_before_disaster",
	"Mini-Games/Uncategorized Games/Seconds Before Disaster": "game_content/minigames/uncategorized_games/seconds_before_disaster",
	"Uncategorized Games/Seconds Before Disaster": "game_content/minigames/uncategorized_games/seconds_before_disaster",
	"Seconds Before Disaster": "game_content/minigames/uncategorized_games/seconds_before_disaster",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Squid Games": "game_content/minigames/uncategorized_games/squid_games",
	"Game Content/Mini-Games/Uncategorized Games/Squid Games": "game_content/minigames/uncategorized_games/squid_games",
	"Mini-Games/Uncategorized Games/Squid Games": "game_content/minigames/uncategorized_games/squid_games",
	"Uncategorized Games/Squid Games": "game_content/minigames/uncategorized_games/squid_games",
	"Squid Games": "game_content/minigames/uncategorized_games/squid_games",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Unhandy Dandies": "game_content/minigames/uncategorized_games/unhandy_dandies",
	"Game Content/Mini-Games/Uncategorized Games/Unhandy Dandies": "game_content/minigames/uncategorized_games/unhandy_dandies",
	"Mini-Games/Uncategorized Games/Unhandy Dandies": "game_content/minigames/uncategorized_games/unhandy_dandies",
	"Uncategorized Games/Unhandy Dandies": "game_content/minigames/uncategorized_games/unhandy_dandies",
	"Unhandy Dandies": "game_content/minigames/uncategorized_games/unhandy_dandies",
	"documentation/Game Content/Mini-Games/Uncategorized Games/Water Striders": "game_content/minigames/uncategorized_games/water_striders",
	"Game Content/Mini-Games/Uncategorized Games/Water Striders": "game_content/minigames/uncategorized_games/water_striders",
	"Mini-Games/Uncategorized Games/Water Striders": "game_content/minigames/uncategorized_games/water_striders",
	"Uncategorized Games/Water Striders": "game_content/minigames/uncategorized_games/water_striders",
	"Water Striders": "game_content/minigames/uncategorized_games/water_striders",
	"documentation/Game Content/Mini-Games/Strategy Games/Little Wars": "game_content/minigames/strategy_games/little_wars",
	"Game Content/Mini-Games/Strategy Games/Little Wars": "game_content/minigames/strategy_games/little_wars",
	"Mini-Games/Strategy Games/Little Wars": "game_content/minigames/strategy_games/little_wars",
	"Strategy Games/Little Wars": "game_content/minigames/strategy_games/little_wars",
	"Little Wars": "game_content/minigames/strategy_games/little_wars",
	"documentation/Game Content/Mini-Games/Strategy Games/Marauders of the Missing Macguffin": "game_content/minigames/strategy_games/marauders_of_the_missing_macguffin",
	"Game Content/Mini-Games/Strategy Games/Marauders of the Missing Macguffin": "game_content/minigames/strategy_games/marauders_of_the_missing_macguffin",
	"Mini-Games/Strategy Games/Marauders of the Missing Macguffin": "game_content/minigames/strategy_games/marauders_of_the_missing_macguffin",
	"Strategy Games/Marauders of the Missing Macguffin": "game_content/minigames/strategy_games/marauders_of_the_missing_macguffin",
	"Marauders of the Missing Macguffin": "game_content/minigames/strategy_games/marauders_of_the_missing_macguffin",
	"documentation/Game Content/Mini-Games/Luck-Based Games/Counting Game": "game_content/minigames/luckbased_games/counting_game",
	"Game Content/Mini-Games/Luck-Based Games/Counting Game": "game_content/minigames/luckbased_games/counting_game",
	"Mini-Games/Luck-Based Games/Counting Game": "game_content/minigames/luckbased_games/counting_game",
	"Luck-Based Games/Counting Game": "game_content/minigames/luckbased_games/counting_game",
	"Counting Game": "game_content/minigames/luckbased_games/counting_game",
	"documentation/Game Content/Mini-Games/Luck-Based Games/Shell Game": "game_content/minigames/luckbased_games/shell_game",
	"Game Content/Mini-Games/Luck-Based Games/Shell Game": "game_content/minigames/luckbased_games/shell_game",
	"Mini-Games/Luck-Based Games/Shell Game": "game_content/minigames/luckbased_games/shell_game",
	"Luck-Based Games/Shell Game": "game_content/minigames/luckbased_games/shell_game",
	"Shell Game": "game_content/minigames/luckbased_games/shell_game",
	"documentation/Game Content/Mini-Games/Luck-Based Games/Spot the Difference": "game_content/minigames/luckbased_games/spot_the_difference",
	"Game Content/Mini-Games/Luck-Based Games/Spot the Difference": "game_content/minigames/luckbased_games/spot_the_difference",
	"Mini-Games/Luck-Based Games/Spot the Difference": "game_content/minigames/luckbased_games/spot_the_difference",
	"Luck-Based Games/Spot the Difference": "game_content/minigames/luckbased_games/spot_the_difference",
	"Spot the Difference": "game_content/minigames/luckbased_games/spot_the_difference",
	"documentation/Game Content/Mini-Games/Action Games/Attack on Ganymede": "game_content/minigames/action_games/attack_on_ganymede",
	"Game Content/Mini-Games/Action Games/Attack on Ganymede": "game_content/minigames/action_games/attack_on_ganymede",
	"Mini-Games/Action Games/Attack on Ganymede": "game_content/minigames/action_games/attack_on_ganymede",
	"Action Games/Attack on Ganymede": "game_content/minigames/action_games/attack_on_ganymede",
	"Attack on Ganymede": "game_content/minigames/action_games/attack_on_ganymede",
	"documentation/Game Content/Mini-Games/Action Games/Club Club": "game_content/minigames/action_games/club_club",
	"Game Content/Mini-Games/Action Games/Club Club": "game_content/minigames/action_games/club_club",
	"Mini-Games/Action Games/Club Club": "game_content/minigames/action_games/club_club",
	"Action Games/Club Club": "game_content/minigames/action_games/club_club",
	"Club Club": "game_content/minigames/action_games/club_club",
	"documentation/Game Content/Mini-Games/Action Games/Hyper Laser Tag": "game_content/minigames/action_games/hyper_laser_tag",
	"Game Content/Mini-Games/Action Games/Hyper Laser Tag": "game_content/minigames/action_games/hyper_laser_tag",
	"Mini-Games/Action Games/Hyper Laser Tag": "game_content/minigames/action_games/hyper_laser_tag",
	"Action Games/Hyper Laser Tag": "game_content/minigames/action_games/hyper_laser_tag",
	"Hyper Laser Tag": "game_content/minigames/action_games/hyper_laser_tag",
	"documentation/Game Content/Mini-Games/Action Games/Quickdraw": "game_content/minigames/action_games/quickdraw",
	"Game Content/Mini-Games/Action Games/Quickdraw": "game_content/minigames/action_games/quickdraw",
	"Mini-Games/Action Games/Quickdraw": "game_content/minigames/action_games/quickdraw",
	"Action Games/Quickdraw": "game_content/minigames/action_games/quickdraw",
	"Quickdraw": "game_content/minigames/action_games/quickdraw",
	"documentation/Game Content/Marketing and Community/Content Examples": "game_content/marketing_and_community/content_examples",
	"Game Content/Marketing and Community/Content Examples": "game_content/marketing_and_community/content_examples",
	"Marketing and Community/Content Examples": "game_content/marketing_and_community/content_examples",
	"Content Examples": "game_content/marketing_and_community/content_examples",
	"documentation/Game Content/Marketing and Community/Social Media Platforms": "game_content/marketing_and_community/social_media_platforms",
	"Game Content/Marketing and Community/Social Media Platforms": "game_content/marketing_and_community/social_media_platforms",
	"Marketing and Community/Social Media Platforms": "game_content/marketing_and_community/social_media_platforms",
	"Social Media Platforms": "game_content/marketing_and_community/social_media_platforms",
	"documentation/Game Content/Marketing and Community/Social Media Strategy": "game_content/marketing_and_community/social_media_strategy",
	"Game Content/Marketing and Community/Social Media Strategy": "game_content/marketing_and_community/social_media_strategy",
	"Marketing and Community/Social Media Strategy": "game_content/marketing_and_community/social_media_strategy",
	"Social Media Strategy": "game_content/marketing_and_community/social_media_strategy",
	"documentation/Game Content/Items & Power-Ups/Universal Items/AOE Delayed Trap": "game_content/items_powerups/universal_items/aoe_delayed_trap",
	"Game Content/Items & Power-Ups/Universal Items/AOE Delayed Trap": "game_content/items_powerups/universal_items/aoe_delayed_trap",
	"Items & Power-Ups/Universal Items/AOE Delayed Trap": "game_content/items_powerups/universal_items/aoe_delayed_trap",
	"Universal Items/AOE Delayed Trap": "game_content/items_powerups/universal_items/aoe_delayed_trap",
	"AOE Delayed Trap": "game_content/items_powerups/universal_items/aoe_delayed_trap",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Banana Peel": "game_content/items_powerups/universal_items/banana_peel",
	"Game Content/Items & Power-Ups/Universal Items/Banana Peel": "game_content/items_powerups/universal_items/banana_peel",
	"Items & Power-Ups/Universal Items/Banana Peel": "game_content/items_powerups/universal_items/banana_peel",
	"Universal Items/Banana Peel": "game_content/items_powerups/universal_items/banana_peel",
	"Banana Peel": "game_content/items_powerups/universal_items/banana_peel",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Battal Buzzer": "game_content/items_powerups/universal_items/battal_buzzer",
	"Game Content/Items & Power-Ups/Universal Items/Battal Buzzer": "game_content/items_powerups/universal_items/battal_buzzer",
	"Items & Power-Ups/Universal Items/Battal Buzzer": "game_content/items_powerups/universal_items/battal_buzzer",
	"Universal Items/Battal Buzzer": "game_content/items_powerups/universal_items/battal_buzzer",
	"Battal Buzzer": "game_content/items_powerups/universal_items/battal_buzzer",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Bounce Off": "game_content/items_powerups/universal_items/bounce_off",
	"Game Content/Items & Power-Ups/Universal Items/Bounce Off": "game_content/items_powerups/universal_items/bounce_off",
	"Items & Power-Ups/Universal Items/Bounce Off": "game_content/items_powerups/universal_items/bounce_off",
	"Universal Items/Bounce Off": "game_content/items_powerups/universal_items/bounce_off",
	"Bounce Off": "game_content/items_powerups/universal_items/bounce_off",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Break The Bank": "game_content/items_powerups/universal_items/break_the_bank",
	"Game Content/Items & Power-Ups/Universal Items/Break The Bank": "game_content/items_powerups/universal_items/break_the_bank",
	"Items & Power-Ups/Universal Items/Break The Bank": "game_content/items_powerups/universal_items/break_the_bank",
	"Universal Items/Break The Bank": "game_content/items_powerups/universal_items/break_the_bank",
	"Break The Bank": "game_content/items_powerups/universal_items/break_the_bank",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Curse Roll": "game_content/items_powerups/universal_items/curse_roll",
	"Game Content/Items & Power-Ups/Universal Items/Curse Roll": "game_content/items_powerups/universal_items/curse_roll",
	"Items & Power-Ups/Universal Items/Curse Roll": "game_content/items_powerups/universal_items/curse_roll",
	"Universal Items/Curse Roll": "game_content/items_powerups/universal_items/curse_roll",
	"Curse Roll": "game_content/items_powerups/universal_items/curse_roll",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Declaration Die": "game_content/items_powerups/universal_items/declaration_die",
	"Game Content/Items & Power-Ups/Universal Items/Declaration Die": "game_content/items_powerups/universal_items/declaration_die",
	"Items & Power-Ups/Universal Items/Declaration Die": "game_content/items_powerups/universal_items/declaration_die",
	"Universal Items/Declaration Die": "game_content/items_powerups/universal_items/declaration_die",
	"Declaration Die": "game_content/items_powerups/universal_items/declaration_die",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Double Up Tennis Ball": "game_content/items_powerups/universal_items/double_up_tennis_ball",
	"Game Content/Items & Power-Ups/Universal Items/Double Up Tennis Ball": "game_content/items_powerups/universal_items/double_up_tennis_ball",
	"Items & Power-Ups/Universal Items/Double Up Tennis Ball": "game_content/items_powerups/universal_items/double_up_tennis_ball",
	"Universal Items/Double Up Tennis Ball": "game_content/items_powerups/universal_items/double_up_tennis_ball",
	"Double Up Tennis Ball": "game_content/items_powerups/universal_items/double_up_tennis_ball",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Flip Flop": "game_content/items_powerups/universal_items/flip_flop",
	"Game Content/Items & Power-Ups/Universal Items/Flip Flop": "game_content/items_powerups/universal_items/flip_flop",
	"Items & Power-Ups/Universal Items/Flip Flop": "game_content/items_powerups/universal_items/flip_flop",
	"Universal Items/Flip Flop": "game_content/items_powerups/universal_items/flip_flop",
	"Flip Flop": "game_content/items_powerups/universal_items/flip_flop",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Game Chooser": "game_content/items_powerups/universal_items/game_chooser",
	"Game Content/Items & Power-Ups/Universal Items/Game Chooser": "game_content/items_powerups/universal_items/game_chooser",
	"Items & Power-Ups/Universal Items/Game Chooser": "game_content/items_powerups/universal_items/game_chooser",
	"Universal Items/Game Chooser": "game_content/items_powerups/universal_items/game_chooser",
	"Game Chooser": "game_content/items_powerups/universal_items/game_chooser",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Game Gambler": "game_content/items_powerups/universal_items/game_gambler",
	"Game Content/Items & Power-Ups/Universal Items/Game Gambler": "game_content/items_powerups/universal_items/game_gambler",
	"Items & Power-Ups/Universal Items/Game Gambler": "game_content/items_powerups/universal_items/game_gambler",
	"Universal Items/Game Gambler": "game_content/items_powerups/universal_items/game_gambler",
	"Game Gambler": "game_content/items_powerups/universal_items/game_gambler",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Golden Mic": "game_content/items_powerups/universal_items/golden_mic",
	"Game Content/Items & Power-Ups/Universal Items/Golden Mic": "game_content/items_powerups/universal_items/golden_mic",
	"Items & Power-Ups/Universal Items/Golden Mic": "game_content/items_powerups/universal_items/golden_mic",
	"Universal Items/Golden Mic": "game_content/items_powerups/universal_items/golden_mic",
	"Golden Mic": "game_content/items_powerups/universal_items/golden_mic",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Growth Item": "game_content/items_powerups/universal_items/growth_item",
	"Game Content/Items & Power-Ups/Universal Items/Growth Item": "game_content/items_powerups/universal_items/growth_item",
	"Items & Power-Ups/Universal Items/Growth Item": "game_content/items_powerups/universal_items/growth_item",
	"Universal Items/Growth Item": "game_content/items_powerups/universal_items/growth_item",
	"Growth Item": "game_content/items_powerups/universal_items/growth_item",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Item Stealing": "game_content/items_powerups/universal_items/item_stealing",
	"Game Content/Items & Power-Ups/Universal Items/Item Stealing": "game_content/items_powerups/universal_items/item_stealing",
	"Items & Power-Ups/Universal Items/Item Stealing": "game_content/items_powerups/universal_items/item_stealing",
	"Universal Items/Item Stealing": "game_content/items_powerups/universal_items/item_stealing",
	"Item Stealing": "game_content/items_powerups/universal_items/item_stealing",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Lavender": "game_content/items_powerups/universal_items/lavender",
	"Game Content/Items & Power-Ups/Universal Items/Lavender": "game_content/items_powerups/universal_items/lavender",
	"Items & Power-Ups/Universal Items/Lavender": "game_content/items_powerups/universal_items/lavender",
	"Universal Items/Lavender": "game_content/items_powerups/universal_items/lavender",
	"Lavender": "game_content/items_powerups/universal_items/lavender",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Pants On Fire": "game_content/items_powerups/universal_items/pants_on_fire",
	"Game Content/Items & Power-Ups/Universal Items/Pants On Fire": "game_content/items_powerups/universal_items/pants_on_fire",
	"Items & Power-Ups/Universal Items/Pants On Fire": "game_content/items_powerups/universal_items/pants_on_fire",
	"Universal Items/Pants On Fire": "game_content/items_powerups/universal_items/pants_on_fire",
	"Pants On Fire": "game_content/items_powerups/universal_items/pants_on_fire",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Phil Bomb": "game_content/items_powerups/universal_items/phil_bomb",
	"Game Content/Items & Power-Ups/Universal Items/Phil Bomb": "game_content/items_powerups/universal_items/phil_bomb",
	"Items & Power-Ups/Universal Items/Phil Bomb": "game_content/items_powerups/universal_items/phil_bomb",
	"Universal Items/Phil Bomb": "game_content/items_powerups/universal_items/phil_bomb",
	"Phil Bomb": "game_content/items_powerups/universal_items/phil_bomb",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Piggy Bank": "game_content/items_powerups/universal_items/piggy_bank",
	"Game Content/Items & Power-Ups/Universal Items/Piggy Bank": "game_content/items_powerups/universal_items/piggy_bank",
	"Items & Power-Ups/Universal Items/Piggy Bank": "game_content/items_powerups/universal_items/piggy_bank",
	"Universal Items/Piggy Bank": "game_content/items_powerups/universal_items/piggy_bank",
	"Piggy Bank": "game_content/items_powerups/universal_items/piggy_bank",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Polarity Inverter": "game_content/items_powerups/universal_items/polarity_inverter",
	"Game Content/Items & Power-Ups/Universal Items/Polarity Inverter": "game_content/items_powerups/universal_items/polarity_inverter",
	"Items & Power-Ups/Universal Items/Polarity Inverter": "game_content/items_powerups/universal_items/polarity_inverter",
	"Universal Items/Polarity Inverter": "game_content/items_powerups/universal_items/polarity_inverter",
	"Polarity Inverter": "game_content/items_powerups/universal_items/polarity_inverter",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Quick Spender": "game_content/items_powerups/universal_items/quick_spender",
	"Game Content/Items & Power-Ups/Universal Items/Quick Spender": "game_content/items_powerups/universal_items/quick_spender",
	"Items & Power-Ups/Universal Items/Quick Spender": "game_content/items_powerups/universal_items/quick_spender",
	"Universal Items/Quick Spender": "game_content/items_powerups/universal_items/quick_spender",
	"Quick Spender": "game_content/items_powerups/universal_items/quick_spender",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Reverse Mushroom": "game_content/items_powerups/universal_items/reverse_mushroom",
	"Game Content/Items & Power-Ups/Universal Items/Reverse Mushroom": "game_content/items_powerups/universal_items/reverse_mushroom",
	"Items & Power-Ups/Universal Items/Reverse Mushroom": "game_content/items_powerups/universal_items/reverse_mushroom",
	"Universal Items/Reverse Mushroom": "game_content/items_powerups/universal_items/reverse_mushroom",
	"Reverse Mushroom": "game_content/items_powerups/universal_items/reverse_mushroom",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Roll Booster": "game_content/items_powerups/universal_items/roll_booster",
	"Game Content/Items & Power-Ups/Universal Items/Roll Booster": "game_content/items_powerups/universal_items/roll_booster",
	"Items & Power-Ups/Universal Items/Roll Booster": "game_content/items_powerups/universal_items/roll_booster",
	"Universal Items/Roll Booster": "game_content/items_powerups/universal_items/roll_booster",
	"Roll Booster": "game_content/items_powerups/universal_items/roll_booster",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Shop Ticket": "game_content/items_powerups/universal_items/shop_ticket",
	"Game Content/Items & Power-Ups/Universal Items/Shop Ticket": "game_content/items_powerups/universal_items/shop_ticket",
	"Items & Power-Ups/Universal Items/Shop Ticket": "game_content/items_powerups/universal_items/shop_ticket",
	"Universal Items/Shop Ticket": "game_content/items_powerups/universal_items/shop_ticket",
	"Shop Ticket": "game_content/items_powerups/universal_items/shop_ticket",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Star Ticket": "game_content/items_powerups/universal_items/star_ticket",
	"Game Content/Items & Power-Ups/Universal Items/Star Ticket": "game_content/items_powerups/universal_items/star_ticket",
	"Items & Power-Ups/Universal Items/Star Ticket": "game_content/items_powerups/universal_items/star_ticket",
	"Universal Items/Star Ticket": "game_content/items_powerups/universal_items/star_ticket",
	"Star Ticket": "game_content/items_powerups/universal_items/star_ticket",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Teleporter": "game_content/items_powerups/universal_items/teleporter",
	"Game Content/Items & Power-Ups/Universal Items/Teleporter": "game_content/items_powerups/universal_items/teleporter",
	"Items & Power-Ups/Universal Items/Teleporter": "game_content/items_powerups/universal_items/teleporter",
	"Universal Items/Teleporter": "game_content/items_powerups/universal_items/teleporter",
	"Teleporter": "game_content/items_powerups/universal_items/teleporter",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Trap Card Trap": "game_content/items_powerups/universal_items/trap_card_trap",
	"Game Content/Items & Power-Ups/Universal Items/Trap Card Trap": "game_content/items_powerups/universal_items/trap_card_trap",
	"Items & Power-Ups/Universal Items/Trap Card Trap": "game_content/items_powerups/universal_items/trap_card_trap",
	"Universal Items/Trap Card Trap": "game_content/items_powerups/universal_items/trap_card_trap",
	"Trap Card Trap": "game_content/items_powerups/universal_items/trap_card_trap",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Trap Protection": "game_content/items_powerups/universal_items/trap_protection",
	"Game Content/Items & Power-Ups/Universal Items/Trap Protection": "game_content/items_powerups/universal_items/trap_protection",
	"Items & Power-Ups/Universal Items/Trap Protection": "game_content/items_powerups/universal_items/trap_protection",
	"Universal Items/Trap Protection": "game_content/items_powerups/universal_items/trap_protection",
	"Trap Protection": "game_content/items_powerups/universal_items/trap_protection",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Trap Square Random Warp": "game_content/items_powerups/universal_items/trap_square_random_warp",
	"Game Content/Items & Power-Ups/Universal Items/Trap Square Random Warp": "game_content/items_powerups/universal_items/trap_square_random_warp",
	"Items & Power-Ups/Universal Items/Trap Square Random Warp": "game_content/items_powerups/universal_items/trap_square_random_warp",
	"Universal Items/Trap Square Random Warp": "game_content/items_powerups/universal_items/trap_square_random_warp",
	"Trap Square Random Warp": "game_content/items_powerups/universal_items/trap_square_random_warp",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Triple Up Tennis Ball": "game_content/items_powerups/universal_items/triple_up_tennis_ball",
	"Game Content/Items & Power-Ups/Universal Items/Triple Up Tennis Ball": "game_content/items_powerups/universal_items/triple_up_tennis_ball",
	"Items & Power-Ups/Universal Items/Triple Up Tennis Ball": "game_content/items_powerups/universal_items/triple_up_tennis_ball",
	"Universal Items/Triple Up Tennis Ball": "game_content/items_powerups/universal_items/triple_up_tennis_ball",
	"Triple Up Tennis Ball": "game_content/items_powerups/universal_items/triple_up_tennis_ball",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Unique Duplicate": "game_content/items_powerups/universal_items/unique_duplicate",
	"Game Content/Items & Power-Ups/Universal Items/Unique Duplicate": "game_content/items_powerups/universal_items/unique_duplicate",
	"Items & Power-Ups/Universal Items/Unique Duplicate": "game_content/items_powerups/universal_items/unique_duplicate",
	"Universal Items/Unique Duplicate": "game_content/items_powerups/universal_items/unique_duplicate",
	"Unique Duplicate": "game_content/items_powerups/universal_items/unique_duplicate",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Wet Fish": "game_content/items_powerups/universal_items/wet_fish",
	"Game Content/Items & Power-Ups/Universal Items/Wet Fish": "game_content/items_powerups/universal_items/wet_fish",
	"Items & Power-Ups/Universal Items/Wet Fish": "game_content/items_powerups/universal_items/wet_fish",
	"Universal Items/Wet Fish": "game_content/items_powerups/universal_items/wet_fish",
	"Wet Fish": "game_content/items_powerups/universal_items/wet_fish",
	"documentation/Game Content/Items & Power-Ups/Universal Items/Wish Bone": "game_content/items_powerups/universal_items/wish_bone",
	"Game Content/Items & Power-Ups/Universal Items/Wish Bone": "game_content/items_powerups/universal_items/wish_bone",
	"Items & Power-Ups/Universal Items/Wish Bone": "game_content/items_powerups/universal_items/wish_bone",
	"Universal Items/Wish Bone": "game_content/items_powerups/universal_items/wish_bone",
	"Wish Bone": "game_content/items_powerups/universal_items/wish_bone",
	"documentation/Game Content/Items & Power-Ups/Enchanted Forest Items/Call Of The Forest": "game_content/items_powerups/enchanted_forest_items/call_of_the_forest",
	"Game Content/Items & Power-Ups/Enchanted Forest Items/Call Of The Forest": "game_content/items_powerups/enchanted_forest_items/call_of_the_forest",
	"Items & Power-Ups/Enchanted Forest Items/Call Of The Forest": "game_content/items_powerups/enchanted_forest_items/call_of_the_forest",
	"Enchanted Forest Items/Call Of The Forest": "game_content/items_powerups/enchanted_forest_items/call_of_the_forest",
	"Call Of The Forest": "game_content/items_powerups/enchanted_forest_items/call_of_the_forest",
	"documentation/Game Content/Items & Power-Ups/Enchanted Forest Items/Grape Vine": "game_content/items_powerups/enchanted_forest_items/grape_vine",
	"Game Content/Items & Power-Ups/Enchanted Forest Items/Grape Vine": "game_content/items_powerups/enchanted_forest_items/grape_vine",
	"Items & Power-Ups/Enchanted Forest Items/Grape Vine": "game_content/items_powerups/enchanted_forest_items/grape_vine",
	"Enchanted Forest Items/Grape Vine": "game_content/items_powerups/enchanted_forest_items/grape_vine",
	"Grape Vine": "game_content/items_powerups/enchanted_forest_items/grape_vine",
	"documentation/Game Content/Items & Power-Ups/Enchanted Forest Items/Mystery Mushroom": "game_content/items_powerups/enchanted_forest_items/mystery_mushroom",
	"Game Content/Items & Power-Ups/Enchanted Forest Items/Mystery Mushroom": "game_content/items_powerups/enchanted_forest_items/mystery_mushroom",
	"Items & Power-Ups/Enchanted Forest Items/Mystery Mushroom": "game_content/items_powerups/enchanted_forest_items/mystery_mushroom",
	"Enchanted Forest Items/Mystery Mushroom": "game_content/items_powerups/enchanted_forest_items/mystery_mushroom",
	"Mystery Mushroom": "game_content/items_powerups/enchanted_forest_items/mystery_mushroom",
	"documentation/Game Content/Items & Power-Ups/Enchanted Forest Items/Pinwheel": "game_content/items_powerups/enchanted_forest_items/pinwheel",
	"Game Content/Items & Power-Ups/Enchanted Forest Items/Pinwheel": "game_content/items_powerups/enchanted_forest_items/pinwheel",
	"Items & Power-Ups/Enchanted Forest Items/Pinwheel": "game_content/items_powerups/enchanted_forest_items/pinwheel",
	"Enchanted Forest Items/Pinwheel": "game_content/items_powerups/enchanted_forest_items/pinwheel",
	"Pinwheel": "game_content/items_powerups/enchanted_forest_items/pinwheel",
	"documentation/Game Content/Items & Power-Ups/Enchanted Forest Items/Reap And Sow": "game_content/items_powerups/enchanted_forest_items/reap_and_sow",
	"Game Content/Items & Power-Ups/Enchanted Forest Items/Reap And Sow": "game_content/items_powerups/enchanted_forest_items/reap_and_sow",
	"Items & Power-Ups/Enchanted Forest Items/Reap And Sow": "game_content/items_powerups/enchanted_forest_items/reap_and_sow",
	"Enchanted Forest Items/Reap And Sow": "game_content/items_powerups/enchanted_forest_items/reap_and_sow",
	"Reap And Sow": "game_content/items_powerups/enchanted_forest_items/reap_and_sow",
	"documentation/Game Content/Items & Power-Ups/Enchanted Forest Items/Stun Spore Hat": "game_content/items_powerups/enchanted_forest_items/stun_spore_hat",
	"Game Content/Items & Power-Ups/Enchanted Forest Items/Stun Spore Hat": "game_content/items_powerups/enchanted_forest_items/stun_spore_hat",
	"Items & Power-Ups/Enchanted Forest Items/Stun Spore Hat": "game_content/items_powerups/enchanted_forest_items/stun_spore_hat",
	"Enchanted Forest Items/Stun Spore Hat": "game_content/items_powerups/enchanted_forest_items/stun_spore_hat",
	"Stun Spore Hat": "game_content/items_powerups/enchanted_forest_items/stun_spore_hat",
	"documentation/Game Content/Items & Power-Ups/Character Specific Items/Catherine Gamer Rage": "game_content/items_powerups/character_specific_items/catherine_gamer_rage",
	"Game Content/Items & Power-Ups/Character Specific Items/Catherine Gamer Rage": "game_content/items_powerups/character_specific_items/catherine_gamer_rage",
	"Items & Power-Ups/Character Specific Items/Catherine Gamer Rage": "game_content/items_powerups/character_specific_items/catherine_gamer_rage",
	"Character Specific Items/Catherine Gamer Rage": "game_content/items_powerups/character_specific_items/catherine_gamer_rage",
	"Catherine Gamer Rage": "game_content/items_powerups/character_specific_items/catherine_gamer_rage",
	"documentation/Game Content/Items & Power-Ups/Character Specific Items/Clyde Traps": "game_content/items_powerups/character_specific_items/clyde_traps",
	"Game Content/Items & Power-Ups/Character Specific Items/Clyde Traps": "game_content/items_powerups/character_specific_items/clyde_traps",
	"Items & Power-Ups/Character Specific Items/Clyde Traps": "game_content/items_powerups/character_specific_items/clyde_traps",
	"Character Specific Items/Clyde Traps": "game_content/items_powerups/character_specific_items/clyde_traps",
	"Clyde Traps": "game_content/items_powerups/character_specific_items/clyde_traps",
	"documentation/Game Content/Items & Power-Ups/Character Specific Items/Doug Buried Bone Map": "game_content/items_powerups/character_specific_items/doug_buried_bone_map",
	"Game Content/Items & Power-Ups/Character Specific Items/Doug Buried Bone Map": "game_content/items_powerups/character_specific_items/doug_buried_bone_map",
	"Items & Power-Ups/Character Specific Items/Doug Buried Bone Map": "game_content/items_powerups/character_specific_items/doug_buried_bone_map",
	"Character Specific Items/Doug Buried Bone Map": "game_content/items_powerups/character_specific_items/doug_buried_bone_map",
	"Doug Buried Bone Map": "game_content/items_powerups/character_specific_items/doug_buried_bone_map",
	"documentation/Game Content/Items & Power-Ups/Character Specific Items/Paulie Plane Ticket": "game_content/items_powerups/character_specific_items/paulie_plane_ticket",
	"Game Content/Items & Power-Ups/Character Specific Items/Paulie Plane Ticket": "game_content/items_powerups/character_specific_items/paulie_plane_ticket",
	"Items & Power-Ups/Character Specific Items/Paulie Plane Ticket": "game_content/items_powerups/character_specific_items/paulie_plane_ticket",
	"Character Specific Items/Paulie Plane Ticket": "game_content/items_powerups/character_specific_items/paulie_plane_ticket",
	"Paulie Plane Ticket": "game_content/items_powerups/character_specific_items/paulie_plane_ticket",
	"documentation/Game Content/Game Modes/Board Only": "game_content/game_modes/board_only",
	"Game Content/Game Modes/Board Only": "game_content/game_modes/board_only",
	"Game Modes/Board Only": "game_content/game_modes/board_only",
	"Board Only": "game_content/game_modes/board_only",
	"documentation/Game Content/Game Modes/Classic": "game_content/game_modes/classic",
	"Game Content/Game Modes/Classic": "game_content/game_modes/classic",
	"Game Modes/Classic": "game_content/game_modes/classic",
	"Classic": "game_content/game_modes/classic",
	"documentation/Game Content/Game Modes/Competitive And Casual Playlists": "game_content/game_modes/competitive_and_casual_playlists",
	"Game Content/Game Modes/Competitive And Casual Playlists": "game_content/game_modes/competitive_and_casual_playlists",
	"Game Modes/Competitive And Casual Playlists": "game_content/game_modes/competitive_and_casual_playlists",
	"Competitive And Casual Playlists": "game_content/game_modes/competitive_and_casual_playlists",
	"documentation/Game Content/Game Modes/Infinite Play": "game_content/game_modes/infinite_play",
	"Game Content/Game Modes/Infinite Play": "game_content/game_modes/infinite_play",
	"Game Modes/Infinite Play": "game_content/game_modes/infinite_play",
	"Infinite Play": "game_content/game_modes/infinite_play",
	"documentation/Game Content/Game Modes/Mini Games Only": "game_content/game_modes/mini_games_only",
	"Game Content/Game Modes/Mini Games Only": "game_content/game_modes/mini_games_only",
	"Game Modes/Mini Games Only": "game_content/game_modes/mini_games_only",
	"Mini Games Only": "game_content/game_modes/mini_games_only",
	"documentation/Game Content/Executive's Corner/Challenges": "game_content/executives_corner/challenges",
	"Game Content/Executive's Corner/Challenges": "game_content/executives_corner/challenges",
	"Executive's Corner/Challenges": "game_content/executives_corner/challenges",
	"Challenges": "game_content/executives_corner/challenges",
	"documentation/Game Content/Executive's Corner/Financial Goals and Timeline": "game_content/executives_corner/financial_goals_and_timeline",
	"Game Content/Executive's Corner/Financial Goals and Timeline": "game_content/executives_corner/financial_goals_and_timeline",
	"Executive's Corner/Financial Goals and Timeline": "game_content/executives_corner/financial_goals_and_timeline",
	"Financial Goals and Timeline": "game_content/executives_corner/financial_goals_and_timeline",
	"documentation/Game Content/Executive's Corner/Kickstarter Planning": "game_content/executives_corner/kickstarter_planning",
	"Game Content/Executive's Corner/Kickstarter Planning": "game_content/executives_corner/kickstarter_planning",
	"Executive's Corner/Kickstarter Planning": "game_content/executives_corner/kickstarter_planning",
	"Kickstarter Planning": "game_content/executives_corner/kickstarter_planning",
	"documentation/Game Content/Development Process/Testing & Quality Assurance/Balance and Gameplay Adjustments": "game_content/development_process/testing_quality_assurance/balance_and_gameplay_adjustments",
	"Game Content/Development Process/Testing & Quality Assurance/Balance and Gameplay Adjustments": "game_content/development_process/testing_quality_assurance/balance_and_gameplay_adjustments",
	"Development Process/Testing & Quality Assurance/Balance and Gameplay Adjustments": "game_content/development_process/testing_quality_assurance/balance_and_gameplay_adjustments",
	"Testing & Quality Assurance/Balance and Gameplay Adjustments": "game_content/development_process/testing_quality_assurance/balance_and_gameplay_adjustments",
	"Balance and Gameplay Adjustments": "game_content/development_process/testing_quality_assurance/balance_and_gameplay_adjustments",
	"documentation/Game Content/Development Process/Testing & Quality Assurance/Community Feedback Mechanisms": "game_content/development_process/testing_quality_assurance/community_feedback_mechanisms",
	"Game Content/Development Process/Testing & Quality Assurance/Community Feedback Mechanisms": "game_content/development_process/testing_quality_assurance/community_feedback_mechanisms",
	"Development Process/Testing & Quality Assurance/Community Feedback Mechanisms": "game_content/development_process/testing_quality_assurance/community_feedback_mechanisms",
	"Testing & Quality Assurance/Community Feedback Mechanisms": "game_content/development_process/testing_quality_assurance/community_feedback_mechanisms",
	"Community Feedback Mechanisms": "game_content/development_process/testing_quality_assurance/community_feedback_mechanisms",
	"documentation/Game Content/Development Process/Testing & Quality Assurance/Internal Playtesting": "game_content/development_process/testing_quality_assurance/internal_playtesting",
	"Game Content/Development Process/Testing & Quality Assurance/Internal Playtesting": "game_content/development_process/testing_quality_assurance/internal_playtesting",
	"Development Process/Testing & Quality Assurance/Internal Playtesting": "game_content/development_process/testing_quality_assurance/internal_playtesting",
	"Testing & Quality Assurance/Internal Playtesting": "game_content/development_process/testing_quality_assurance/internal_playtesting",
	"Internal Playtesting": "game_content/development_process/testing_quality_assurance/internal_playtesting",
	"documentation/Game Content/Development Process/Programming & Coding/Board Logic": "game_content/development_process/programming_coding/board_logic",
	"Game Content/Development Process/Programming & Coding/Board Logic": "game_content/development_process/programming_coding/board_logic",
	"Development Process/Programming & Coding/Board Logic": "game_content/development_process/programming_coding/board_logic",
	"Programming & Coding/Board Logic": "game_content/development_process/programming_coding/board_logic",
	"Board Logic": "game_content/development_process/programming_coding/board_logic",
	"documentation/Game Content/Development Process/Programming & Coding/Mini-Game Logic": "game_content/development_process/programming_coding/minigame_logic",
	"Game Content/Development Process/Programming & Coding/Mini-Game Logic": "game_content/development_process/programming_coding/minigame_logic",
	"Development Process/Programming & Coding/Mini-Game Logic": "game_content/development_process/programming_coding/minigame_logic",
	"Programming & Coding/Mini-Game Logic": "game_content/development_process/programming_coding/minigame_logic",
	"Mini-Game Logic": "game_content/development_process/programming_coding/minigame_logic",
	"documentation/Game Content/Development Process/Programming & Coding/Networking or Multiplayer": "game_content/development_process/programming_coding/networking_or_multiplayer",
	"Game Content/Development Process/Programming & Coding/Networking or Multiplayer": "game_content/development_process/programming_coding/networking_or_multiplayer",
	"Development Process/Programming & Coding/Networking or Multiplayer": "game_content/development_process/programming_coding/networking_or_multiplayer",
	"Programming & Coding/Networking or Multiplayer": "game_content/development_process/programming_coding/networking_or_multiplayer",
	"Networking or Multiplayer": "game_content/development_process/programming_coding/networking_or_multiplayer",
	"documentation/Game Content/Development Process/Programming & Coding/Workshop Support": "game_content/development_process/programming_coding/workshop_support",
	"Game Content/Development Process/Programming & Coding/Workshop Support": "game_content/development_process/programming_coding/workshop_support",
	"Development Process/Programming & Coding/Workshop Support": "game_content/development_process/programming_coding/workshop_support",
	"Programming & Coding/Workshop Support": "game_content/development_process/programming_coding/workshop_support",
	"Workshop Support": "game_content/development_process/programming_coding/workshop_support",
	"documentation/Game Content/Development Process/Planning & Management/Kickstarter Campaign Materials/Drafts and Feedback": "game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback",
	"Game Content/Development Process/Planning & Management/Kickstarter Campaign Materials/Drafts and Feedback": "game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback",
	"Development Process/Planning & Management/Kickstarter Campaign Materials/Drafts and Feedback": "game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback",
	"Planning & Management/Kickstarter Campaign Materials/Drafts and Feedback": "game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback",
	"Kickstarter Campaign Materials/Drafts and Feedback": "game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback",
	"Drafts and Feedback": "game_content/development_process/planning_management/kickstarter_campaign_materials/drafts_and_feedback",
	"documentation/Game Content/Development Process/Planning & Management/Kickstarter Campaign Materials/Trailer Content Checklists": "game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists",
	"Game Content/Development Process/Planning & Management/Kickstarter Campaign Materials/Trailer Content Checklists": "game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists",
	"Development Process/Planning & Management/Kickstarter Campaign Materials/Trailer Content Checklists": "game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists",
	"Planning & Management/Kickstarter Campaign Materials/Trailer Content Checklists": "game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists",
	"Kickstarter Campaign Materials/Trailer Content Checklists": "game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists",
	"Trailer Content Checklists": "game_content/development_process/planning_management/kickstarter_campaign_materials/trailer_content_checklists",
	"documentation/Game Content/Development Process/Planning & Management/Documentation and Meetings": "game_content/development_process/planning_management/documentation_and_meetings",
	"Game Content/Development Process/Planning & Management/Documentation and Meetings": "game_content/development_process/planning_management/documentation_and_meetings",
	"Development Process/Planning & Management/Documentation and Meetings": "game_content/development_process/planning_management/documentation_and_meetings",
	"Planning & Management/Documentation and Meetings": "game_content/development_process/planning_management/documentation_and_meetings",
	"Documentation and Meetings": "game_content/development_process/planning_management/documentation_and_meetings",
	"documentation/Game Content/Development Process/Art & Design/Character and Map Asset Creation": "game_content/development_process/art_design/character_and_map_asset_creation",
	"Game Content/Development Process/Art & Design/Character and Map Asset Creation": "game_content/development_process/art_design/character_and_map_asset_creation",
	"Development Process/Art & Design/Character and Map Asset Creation": "game_content/development_process/art_design/character_and_map_asset_creation",
	"Art & Design/Character and Map Asset Creation": "game_content/development_process/art_design/character_and_map_asset_creation",
	"Character and Map Asset Creation": "game_content/development_process/art_design/character_and_map_asset_creation",
	"documentation/Game Content/Development Process/Art & Design/General Art Process": "game_content/development_process/art_design/general_art_process",
	"Game Content/Development Process/Art & Design/General Art Process": "game_content/development_process/art_design/general_art_process",
	"Development Process/Art & Design/General Art Process": "game_content/development_process/art_design/general_art_process",
	"Art & Design/General Art Process": "game_content/development_process/art_design/general_art_process",
	"General Art Process": "game_content/development_process/art_design/general_art_process",
	"documentation/Game Content/Development Process/Art & Design/Shader and Texture Libraries": "game_content/development_process/art_design/shader_and_texture_libraries",
	"Game Content/Development Process/Art & Design/Shader and Texture Libraries": "game_content/development_process/art_design/shader_and_texture_libraries",
	"Development Process/Art & Design/Shader and Texture Libraries": "game_content/development_process/art_design/shader_and_texture_libraries",
	"Art & Design/Shader and Texture Libraries": "game_content/development_process/art_design/shader_and_texture_libraries",
	"Shader and Texture Libraries": "game_content/development_process/art_design/shader_and_texture_libraries",
	"documentation/Game Content/Critters/Board Specific Critters/Enchanted Forest Critters": "game_content/critters/board_specific_critters/enchanted_forest_critters",
	"Game Content/Critters/Board Specific Critters/Enchanted Forest Critters": "game_content/critters/board_specific_critters/enchanted_forest_critters",
	"Critters/Board Specific Critters/Enchanted Forest Critters": "game_content/critters/board_specific_critters/enchanted_forest_critters",
	"Board Specific Critters/Enchanted Forest Critters": "game_content/critters/board_specific_critters/enchanted_forest_critters",
	"Enchanted Forest Critters": "game_content/critters/board_specific_critters/enchanted_forest_critters",
	"documentation/Game Content/Critters/Board Specific Critters/Space Station Critters": "game_content/critters/board_specific_critters/space_station_critters",
	"Game Content/Critters/Board Specific Critters/Space Station Critters": "game_content/critters/board_specific_critters/space_station_critters",
	"Critters/Board Specific Critters/Space Station Critters": "game_content/critters/board_specific_critters/space_station_critters",
	"Board Specific Critters/Space Station Critters": "game_content/critters/board_specific_critters/space_station_critters",
	"Space Station Critters": "game_content/critters/board_specific_critters/space_station_critters",
	"documentation/Game Content/Critters/Board Specific Critters/Wetworld Critters": "game_content/critters/board_specific_critters/wetworld_critters",
	"Game Content/Critters/Board Specific Critters/Wetworld Critters": "game_content/critters/board_specific_critters/wetworld_critters",
	"Critters/Board Specific Critters/Wetworld Critters": "game_content/critters/board_specific_critters/wetworld_critters",
	"Board Specific Critters/Wetworld Critters": "game_content/critters/board_specific_critters/wetworld_critters",
	"Wetworld Critters": "game_content/critters/board_specific_critters/wetworld_critters",
	"documentation/Game Content/Critters/Generic Creatures Role and Behavior": "game_content/critters/generic_creatures_role_and_behavior",
	"Game Content/Critters/Generic Creatures Role and Behavior": "game_content/critters/generic_creatures_role_and_behavior",
	"Critters/Generic Creatures Role and Behavior": "game_content/critters/generic_creatures_role_and_behavior",
	"Generic Creatures Role and Behavior": "game_content/critters/generic_creatures_role_and_behavior",
	"documentation/Game Content/Community & Workshop/Steam Workshop Integration": "game_content/community_workshop/steam_workshop_integration",
	"Game Content/Community & Workshop/Steam Workshop Integration": "game_content/community_workshop/steam_workshop_integration",
	"Community & Workshop/Steam Workshop Integration": "game_content/community_workshop/steam_workshop_integration",
	"Steam Workshop Integration": "game_content/community_workshop/steam_workshop_integration",
	"documentation/Game Content/Community & Workshop/Workshop Asset Templates": "game_content/community_workshop/workshop_asset_templates",
	"Game Content/Community & Workshop/Workshop Asset Templates": "game_content/community_workshop/workshop_asset_templates",
	"Community & Workshop/Workshop Asset Templates": "game_content/community_workshop/workshop_asset_templates",
	"Workshop Asset Templates": "game_content/community_workshop/workshop_asset_templates",
	"documentation/Game Content/Characters/Playable Characters/Antony": "game_content/characters/playable_characters/antony",
	"Game Content/Characters/Playable Characters/Antony": "game_content/characters/playable_characters/antony",
	"Characters/Playable Characters/Antony": "game_content/characters/playable_characters/antony",
	"Playable Characters/Antony": "game_content/characters/playable_characters/antony",
	"Antony": "game_content/characters/playable_characters/antony",
	"documentation/Game Content/Characters/Playable Characters/Bonnie": "game_content/characters/playable_characters/bonnie",
	"Game Content/Characters/Playable Characters/Bonnie": "game_content/characters/playable_characters/bonnie",
	"Characters/Playable Characters/Bonnie": "game_content/characters/playable_characters/bonnie",
	"Playable Characters/Bonnie": "game_content/characters/playable_characters/bonnie",
	"Bonnie": "game_content/characters/playable_characters/bonnie",
	"documentation/Game Content/Characters/Playable Characters/Catherine": "game_content/characters/playable_characters/catherine",
	"Game Content/Characters/Playable Characters/Catherine": "game_content/characters/playable_characters/catherine",
	"Characters/Playable Characters/Catherine": "game_content/characters/playable_characters/catherine",
	"Playable Characters/Catherine": "game_content/characters/playable_characters/catherine",
	"Catherine": "game_content/characters/playable_characters/catherine",
	"documentation/Game Content/Characters/Playable Characters/Clyde": "game_content/characters/playable_characters/clyde",
	"Game Content/Characters/Playable Characters/Clyde": "game_content/characters/playable_characters/clyde",
	"Characters/Playable Characters/Clyde": "game_content/characters/playable_characters/clyde",
	"Playable Characters/Clyde": "game_content/characters/playable_characters/clyde",
	"Clyde": "game_content/characters/playable_characters/clyde",
	"documentation/Game Content/Characters/Playable Characters/Dallas": "game_content/characters/playable_characters/dallas",
	"Game Content/Characters/Playable Characters/Dallas": "game_content/characters/playable_characters/dallas",
	"Characters/Playable Characters/Dallas": "game_content/characters/playable_characters/dallas",
	"Playable Characters/Dallas": "game_content/characters/playable_characters/dallas",
	"Dallas": "game_content/characters/playable_characters/dallas",
	"documentation/Game Content/Characters/Playable Characters/Doug": "game_content/characters/playable_characters/doug",
	"Game Content/Characters/Playable Characters/Doug": "game_content/characters/playable_characters/doug",
	"Characters/Playable Characters/Doug": "game_content/characters/playable_characters/doug",
	"Playable Characters/Doug": "game_content/characters/playable_characters/doug",
	"Doug": "game_content/characters/playable_characters/doug",
	"documentation/Game Content/Characters/Playable Characters/Draco": "game_content/characters/playable_characters/draco",
	"Game Content/Characters/Playable Characters/Draco": "game_content/characters/playable_characters/draco",
	"Characters/Playable Characters/Draco": "game_content/characters/playable_characters/draco",
	"Playable Characters/Draco": "game_content/characters/playable_characters/draco",
	"Draco": "game_content/characters/playable_characters/draco",
	"documentation/Game Content/Characters/Playable Characters/Finn": "game_content/characters/playable_characters/finn",
	"Game Content/Characters/Playable Characters/Finn": "game_content/characters/playable_characters/finn",
	"Characters/Playable Characters/Finn": "game_content/characters/playable_characters/finn",
	"Playable Characters/Finn": "game_content/characters/playable_characters/finn",
	"Finn": "game_content/characters/playable_characters/finn",
	"documentation/Game Content/Characters/Playable Characters/Paulie": "game_content/characters/playable_characters/paulie",
	"Game Content/Characters/Playable Characters/Paulie": "game_content/characters/playable_characters/paulie",
	"Characters/Playable Characters/Paulie": "game_content/characters/playable_characters/paulie",
	"Playable Characters/Paulie": "game_content/characters/playable_characters/paulie",
	"Paulie": "game_content/characters/playable_characters/paulie",
	"documentation/Game Content/Characters/Playable Characters/Renard": "game_content/characters/playable_characters/renard",
	"Game Content/Characters/Playable Characters/Renard": "game_content/characters/playable_characters/renard",
	"Characters/Playable Characters/Renard": "game_content/characters/playable_characters/renard",
	"Playable Characters/Renard": "game_content/characters/playable_characters/renard",
	"Renard": "game_content/characters/playable_characters/renard",
	"documentation/Game Content/Characters/Non-Playable Characters/Critters": "game_content/characters/nonplayable_characters/critters",
	"Game Content/Characters/Non-Playable Characters/Critters": "game_content/characters/nonplayable_characters/critters",
	"Characters/Non-Playable Characters/Critters": "game_content/characters/nonplayable_characters/critters",
	"Non-Playable Characters/Critters": "game_content/characters/nonplayable_characters/critters",
	"Critters": "game_content/characters/nonplayable_characters/critters",
	"documentation/Game Content/Characters/Non-Playable Characters/Host Character": "game_content/characters/nonplayable_characters/host_character",
	"Game Content/Characters/Non-Playable Characters/Host Character": "game_content/characters/nonplayable_characters/host_character",
	"Characters/Non-Playable Characters/Host Character": "game_content/characters/nonplayable_characters/host_character",
	"Non-Playable Characters/Host Character": "game_content/characters/nonplayable_characters/host_character",
	"Host Character": "game_content/characters/nonplayable_characters/host_character",
	"documentation/Game Content/Characters/Non-Playable Characters/Shopkeepers": "game_content/characters/nonplayable_characters/shopkeepers",
	"Game Content/Characters/Non-Playable Characters/Shopkeepers": "game_content/characters/nonplayable_characters/shopkeepers",
	"Characters/Non-Playable Characters/Shopkeepers": "game_content/characters/nonplayable_characters/shopkeepers",
	"Non-Playable Characters/Shopkeepers": "game_content/characters/nonplayable_characters/shopkeepers",
	"Shopkeepers": "game_content/characters/nonplayable_characters/shopkeepers",
	"documentation/Game Content/Characters/Non-Playable Characters/Villain Characters": "game_content/characters/nonplayable_characters/villain_characters",
	"Game Content/Characters/Non-Playable Characters/Villain Characters": "game_content/characters/nonplayable_characters/villain_characters",
	"Characters/Non-Playable Characters/Villain Characters": "game_content/characters/nonplayable_characters/villain_characters",
	"Non-Playable Characters/Villain Characters": "game_content/characters/nonplayable_characters/villain_characters",
	"Villain Characters": "game_content/characters/nonplayable_characters/villain_characters",
	"documentation/Game Content/Boards/Theme-Specific Boards/Enchanted Forest Board": "game_content/boards/themespecific_boards/enchanted_forest_board",
	"Game Content/Boards/Theme-Specific Boards/Enchanted Forest Board": "game_content/boards/themespecific_boards/enchanted_forest_board",
	"Boards/Theme-Specific Boards/Enchanted Forest Board": "game_content/boards/themespecific_boards/enchanted_forest_board",
	"Theme-Specific Boards/Enchanted Forest Board": "game_content/boards/themespecific_boards/enchanted_forest_board",
	"Enchanted Forest Board": "game_content/boards/themespecific_boards/enchanted_forest_board",
	"documentation/Game Content/Boards/Theme-Specific Boards/Space Station Board": "game_content/boards/themespecific_boards/space_station_board",
	"Game Content/Boards/Theme-Specific Boards/Space Station Board": "game_content/boards/themespecific_boards/space_station_board",
	"Boards/Theme-Specific Boards/Space Station Board": "game_content/boards/themespecific_boards/space_station_board",
	"Theme-Specific Boards/Space Station Board": "game_content/boards/themespecific_boards/space_station_board",
	"Space Station Board": "game_content/boards/themespecific_boards/space_station_board",
	"documentation/Game Content/Boards/Theme-Specific Boards/Wetworld Board": "game_content/boards/themespecific_boards/wetworld_board",
	"Game Content/Boards/Theme-Specific Boards/Wetworld Board": "game_content/boards/themespecific_boards/wetworld_board",
	"Boards/Theme-Specific Boards/Wetworld Board": "game_content/boards/themespecific_boards/wetworld_board",
	"Theme-Specific Boards/Wetworld Board": "game_content/boards/themespecific_boards/wetworld_board",
	"Wetworld Board": "game_content/boards/themespecific_boards/wetworld_board",
	"documentation/Game Content/Boards/Board Events and Gimmicks": "game_content/boards/board_events_and_gimmicks",
	"Game Content/Boards/Board Events and Gimmicks": "game_content/boards/board_events_and_gimmicks",
	"Boards/Board Events and Gimmicks": "game_content/boards/board_events_and_gimmicks",
	"Board Events and Gimmicks": "game_content/boards/board_events_and_gimmicks",
	"documentation/Game Content/Boards/General Board Features": "game_content/boards/general_board_features",
	"Game Content/Boards/General Board Features": "game_content/boards/general_board_features",
	"Boards/General Board Features": "game_content/boards/general_board_features",
	"General Board Features": "game_content/boards/general_board_features",
	"documentation/Naive Bayes Classifier": "naive_bayes_classifier",
	"Naive Bayes Classifier": "naive_bayes_classifier"
};
