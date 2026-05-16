class GamepadInput {
    constructor(callbacks) {
        this.callbacks = callbacks || {};
        this.lastAxisX = 0;
        this.lastAxisY = 0;
        this.lastState = {};
        this.running = false;
        this.poll = this.poll.bind(this);
    }

    start() {
        this.running = true;
        requestAnimationFrame(this.poll);
    }

    stop() {
        this.running = false;
    }

    poll() {
        if (!this.running) return;
        const pads = navigator.getGamepads();
        const gp = pads[0];

        if (gp) {
            const axisX = gp.axes[0] || 0;
            const axisY = gp.axes[1] || 0;
            const dpadUp = gp.buttons.length > 12 ? gp.buttons[12].pressed : false;
            const dpadDown = gp.buttons.length > 13 ? gp.buttons[13].pressed : false;
            const dpadLeft = gp.buttons.length > 14 ? gp.buttons[14].pressed : false;
            const dpadRight = gp.buttons.length > 15 ? gp.buttons[15].pressed : false;

            const bPressed = gp.buttons[0] && gp.buttons[0].pressed;
            const aPressed = gp.buttons[1] && gp.buttons[1].pressed;
            const yPressed = gp.buttons[2] && gp.buttons[2].pressed;
            const xPressed = gp.buttons[3] && gp.buttons[3].pressed;
            const selectPressed = gp.buttons[8] && gp.buttons[8].pressed;
            const startPressed = gp.buttons[9] && gp.buttons[9].pressed;

            const actionPressed = aPressed || xPressed;

            if ((axisY < -0.5 || dpadUp) && this.lastAxisY >= -0.5 && !this.lastState.dpadUp) {
                if (this.callbacks.onUp) this.callbacks.onUp();
            }
            if ((axisY > 0.5 || dpadDown) && this.lastAxisY <= 0.5 && !this.lastState.dpadDown) {
                if (this.callbacks.onDown) this.callbacks.onDown();
            }
            if ((axisX < -0.5 || dpadLeft) && this.lastAxisX >= -0.5 && !this.lastState.dpadLeft) {
                if (this.callbacks.onLeft) this.callbacks.onLeft();
            }
            if ((axisX > 0.5 || dpadRight) && this.lastAxisX <= 0.5 && !this.lastState.dpadRight) {
                if (this.callbacks.onRight) this.callbacks.onRight();
            }

            if (actionPressed && !this.lastState.actionPressed) {
                if (this.callbacks.onAction) this.callbacks.onAction();
            }
            if (bPressed && !this.lastState.bPressed) {
                if (this.callbacks.onBack) this.callbacks.onBack();
            }
            if (yPressed && !this.lastState.yPressed) {
                if (this.callbacks.onHome) this.callbacks.onHome();
            }
            if (startPressed && selectPressed && (!this.lastState.startPressed || !this.lastState.selectPressed)) {
                if (this.callbacks.onStartSelect) this.callbacks.onStartSelect();
            }

            this.lastAxisX = axisX;
            this.lastAxisY = axisY;
            this.lastState = {
                dpadUp, dpadDown, dpadLeft, dpadRight,
                actionPressed, bPressed, yPressed, startPressed, selectPressed
            };
        }
        requestAnimationFrame(this.poll);
    }
}
