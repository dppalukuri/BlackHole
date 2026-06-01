export interface GratuityResult {
  gratuityAmount: number;
  basicSalary: number;
  yearsOfService: number;
}

/** UAE end-of-service gratuity (Federal Decree-Law No. 33 of 2021) */
export function uaeGratuity(
  basicMonthlySalary: number,
  yearsOfService: number
): GratuityResult {
  if (yearsOfService < 1) {
    return { gratuityAmount: 0, basicSalary: basicMonthlySalary, yearsOfService };
  }

  const dailyWage = basicMonthlySalary / 30;
  let gratuity = 0;

  if (yearsOfService <= 5) {
    gratuity = dailyWage * 21 * yearsOfService;
  } else {
    gratuity = dailyWage * 21 * 5 + dailyWage * 30 * (yearsOfService - 5);
  }

  // Cap: total gratuity cannot exceed 2 years' salary
  const cap = basicMonthlySalary * 24;
  gratuity = Math.min(gratuity, cap);

  return {
    gratuityAmount: gratuity,
    basicSalary: basicMonthlySalary,
    yearsOfService,
  };
}

/** India gratuity (Payment of Gratuity Act, 1972) */
export function indiaGratuity(
  lastDrawnSalary: number,
  yearsOfService: number
): GratuityResult {
  // Formula: (15 * last drawn salary * years of service) / 26
  if (yearsOfService < 5) {
    return { gratuityAmount: 0, basicSalary: lastDrawnSalary, yearsOfService };
  }
  const gratuity = (15 * lastDrawnSalary * yearsOfService) / 26;
  // Cap: max 20 lakh (as per current rules)
  const capped = Math.min(gratuity, 2000000);
  return { gratuityAmount: capped, basicSalary: lastDrawnSalary, yearsOfService };
}

/** Simple VAT calculation */
export function calculateVAT(
  amount: number,
  vatRate: number,
  inclusive: boolean = false
): { netAmount: number; vatAmount: number; totalAmount: number } {
  if (inclusive) {
    const netAmount = amount / (1 + vatRate / 100);
    const vatAmount = amount - netAmount;
    return { netAmount, vatAmount, totalAmount: amount };
  }
  const vatAmount = amount * (vatRate / 100);
  return { netAmount: amount, vatAmount, totalAmount: amount + vatAmount };
}
