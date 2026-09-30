document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#register-form');
    if (!form) {
        return;
    }

    const fullName = document.querySelector('#full-name');
    const phoneNumber = document.querySelector('#phone-number');
    const pin = document.querySelector('#pin');
    const confirmPin = document.querySelector('#confirm-pin');

    [phoneNumber, pin, confirmPin].forEach((input) => {
        input.addEventListener('input', () => {
            input.value = input.value.replace(/\D/g, '');
        });
    });

    document.querySelectorAll('.pin-toggle').forEach((button) => {
        button.addEventListener('click', () => {
            const input = document.querySelector(`#${button.dataset.target}`);
            const isVisible = input.type === 'text';
            input.type = isVisible ? 'password' : 'text';
            button.textContent = isVisible ? 'Show PIN' : 'Hide PIN';
        });
    });

    form.addEventListener('submit', (event) => {
        const nameIsValid = /^[A-Za-z ]+$/.test(fullName.value.trim());
        const phoneIsValid = /^[6-9]\d{9}$/.test(phoneNumber.value);
        const pinIsValid = /^\d{4}$/.test(pin.value);
        const pinsMatch = pin.value === confirmPin.value;

        document.querySelector('#name-error').textContent = nameIsValid ? '' : 'Enter your name using letters and spaces only.';
        document.querySelector('#phone-error').textContent = phoneIsValid ? '' : 'Enter a valid 10-digit Indian mobile number.';
        document.querySelector('#pin-error').textContent = pinIsValid ? '' : 'PIN must contain exactly 4 digits.';
        document.querySelector('#confirm-pin-error').textContent = pinsMatch ? '' : 'The PINs do not match.';

        [fullName, phoneNumber, pin, confirmPin].forEach((input) => input.classList.remove('input-error'));
        if (!nameIsValid) fullName.classList.add('input-error');
        if (!phoneIsValid) phoneNumber.classList.add('input-error');
        if (!pinIsValid) pin.classList.add('input-error');
        if (!pinsMatch) confirmPin.classList.add('input-error');

        if (!nameIsValid || !phoneIsValid || !pinIsValid || !pinsMatch) {
            event.preventDefault();
            [fullName, phoneNumber, pin, confirmPin].find((input) => input.classList.contains('input-error')).focus();
        }
    });
});
