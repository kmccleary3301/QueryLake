
import board_only from "./board_only"; //MD IDENTIFIED
import classic from "./classic"; //MD IDENTIFIED
import competitive_and_casual_playlists from "./competitive_and_casual_playlists"; //MD IDENTIFIED
import infinite_play from "./infinite_play"; //MD IDENTIFIED
import mini_games_only from "./mini_games_only"; //MD IDENTIFIED


const game_modes = {
	"board_only": board_only,
	"classic": classic,
	"competitive_and_casual_playlists": competitive_and_casual_playlists,
	"infinite_play": infinite_play,
	"mini_games_only": mini_games_only
};

export default game_modes;
