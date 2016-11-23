DROP TABLE IF EXISTS songs;
CREATE TABLE songs (
songID int NOT NULL AUTO_INCREMENT,
songTitle varchar(50) NOT NULL,
youTubeURL varchar(200) NOT NULL,
userID varchar(20) NOT NULL,
CONSTRAINT songs_pk PRIMARY KEY (songID)
);
#INSERT INTO songs VALUES
#('The Trooper','https://www.youtube.com/watch?v=2G5rfPISIwo');
