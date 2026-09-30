document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('#login-form');
    const accountNumber = document.querySelector('#account-number');
    const pin = document.querySelector('#pin');
    const accountError = document.querySelector('#account-number-error');
    const pinError = document.querySelector('#pin-error');
    const pinToggle = document.querySelector('#pin-toggle');

    // Keep numeric fields numeric even when a value is pasted.
    accountNumber.addEventListener('input', () => {
        accountNumber.value = accountNumber.value.replace(/\D/g, '').slice(0, 16);
    });

    pin.addEventListener('input', () => {
        pin.value = pin.value.replace(/\D/g, '').slice(0, 4);
    });

    pinToggle.addEventListener('click', () => {
        const pinIsVisible = pin.type === 'text';
        pin.type = pinIsVisible ? 'password' : 'text';
        pinToggle.textContent = pinIsVisible ? 'Show PIN' : 'Hide PIN';
        pinToggle.setAttribute('aria-pressed', String(!pinIsVisible));
    });

    form.addEventListener('submit', (event) => {
        const accountIsValid = /^\d{6,16}$/.test(accountNumber.value);
        const pinIsValid = /^\d{4}$/.test(pin.value);

        accountError.textContent = accountIsValid
            ? ''
            : accountNumber.value
                ? 'Enter a valid account number using 6 to 16 digits.'
                : 'Please enter your account number.';
        pinError.textContent = pinIsValid
            ? ''
            : 'Please enter exactly 4 digits for your PIN.';

        accountNumber.classList.toggle('input-error', !accountIsValid);
        pin.classList.toggle('input-error', !pinIsValid);
        accountNumber.setAttribute('aria-invalid', String(!accountIsValid));
        pin.setAttribute('aria-invalid', String(!pinIsValid));

        if (!accountIsValid || !pinIsValid) {
            event.preventDefault();
            (accountIsValid ? pin : accountNumber).focus();
        }
    });
});
