document.addEventListener('DOMContentLoaded', function() {
    const datepicker = document.getElementById('datepicker');
    if (!datepicker) return;
    
    const datasComFrequencia = window.datasComFrequencia || [];
    
    flatpickr(datepicker, {
        dateFormat: "Y-m-d",
        defaultDate: datepicker.value,
        altInput: true,
        altFormat: "d/m/Y",
        locale: "pt",
        onDayCreate: function(dObj, dStr, fp, dayElem) {
            const ano = dayElem.dateObj.getFullYear();
            const mes = String(dayElem.dateObj.getMonth() + 1).padStart(2, '0');
            const dia = String(dayElem.dateObj.getDate()).padStart(2, '0');
            const dataFormatada = `${ano}-${mes}-${dia}`;
            
            if (datasComFrequencia.includes(dataFormatada)) {
                dayElem.style.backgroundColor = '#3b82f6';
                dayElem.style.color = 'white';
                dayElem.style.borderRadius = '50%';
                dayElem.style.fontWeight = 'bold';
            }
        },
        onChange: function(selectedDates, dateStr, instance) {
            window.location.href = `?data=${dateStr}`;
        }
    });
});