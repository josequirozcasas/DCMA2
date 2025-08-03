def format_currency(amount):
    """
    Formata um valor numérico como moeda em reais (R$).

    Args:
        amount (float): Valor a ser formatado.

    Returns:
        str: Valor formatado como R$ XXX.XXX,XX.
    """
    return f'R${amount:,.2f}'.replace('.', 'X').replace(',', '.').replace('X', ',')