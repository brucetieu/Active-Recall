alert('Counting Down!');

const StartingMin = my_var;
let time = StartingMin * 60;

const countdownEl = document.getElementById('countdown');

function updateCountdown() {
    const minutes = Math.floor(time / 60);
    let seconds = time % 60;

    seconds = seconds < 10 ? '0' + seconds : seconds;

    countdownEl.innerHTML = '${minutes}:${seconds}';
    time --;

    time = time < 0 ? 0 : time;
}
