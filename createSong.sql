DELIMITER //
DROP PROCEDURE IF EXISTS createSong //

CREATE PROCEDURE createSong(IN cSongTitle varchar(50), IN cYouTubeURL varchar(400), IN cUserID varchar(20))
BEGIN
INSERT INTO songs (songTitle, youTubeURL, userID) VALUES (cSongTitle, cYouTubeURL, cUserID);
END //
DELIMITER ;
