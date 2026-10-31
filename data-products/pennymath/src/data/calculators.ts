/**
 * Every calculator on the site, in one place. The homepage, the country pages,
 * the search box and the sitemap of links all read from this list, so adding a
 * calculator here is what makes it findable.
 */
export type Country = 'India' | 'UAE' | 'UK' | 'US';
export type TopicId = 'loans' | 'invest' | 'tax' | 'property' | 'other';

export interface CalculatorEntry {
  path: string;
  name: string;
  country: Country;
  topic: TopicId;
  desc: string;
  tags: string;
}

export const COUNTRIES: Array<{ name: Country; path: string }> = [
  { name: 'India', path: '/india/' },
  { name: 'UAE', path: '/uae/' },
  { name: 'UK', path: '/uk/' },
  { name: 'US', path: '/us/' },
];

export const TOPICS: Array<{ id: TopicId; name: string; icon: string }> = [
  { id: 'loans', name: 'Home loans and mortgages', icon: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9.5h13V10"/><path d="M10 19.5v-5h4v5"/>' },
  { id: 'invest', name: 'Investing and retirement', icon: '<path d="M3 17l5.5-6 4 3.5L21 6"/><path d="M15.5 6H21v5.5"/>' },
  { id: 'tax', name: 'Tax and salary', icon: '<path d="M6 3h12v18l-3-1.8-3 1.8-3-1.8L6 21z"/><path d="M9.5 8h5M9.5 12h5"/>' },
  { id: 'property', name: 'Property', icon: '<path d="M5 21V5.5L13 3v18"/><path d="M13 9.5l6 2V21"/><path d="M3 21h18"/><path d="M8.5 8.5h1M8.5 12.5h1M8.5 16.5h1"/>' },
  { id: 'other', name: 'Other loans and transfers', icon: '<path d="M4 8h14"/><path d="m14.5 4.5 3.5 3.5-3.5 3.5"/><path d="M20 16H6"/><path d="m9.5 12.5L6 16l3.5 3.5"/>' },
];

export const CALCULATORS: CalculatorEntry[] = [
  // Home loans and mortgages
  { path: '/india/emi-calculator/', name: 'EMI Calculator', country: 'India', topic: 'loans', desc: 'Work out the EMI on a home, car or personal loan.', tags: 'emi loan home car personal monthly installment' },
  { path: '/india/home-loan-eligibility-calculator/', name: 'Home Loan Eligibility', country: 'India', topic: 'loans', desc: 'See the loan and property price your salary and savings support.', tags: 'home loan eligibility salary foir ltv affordability down payment how much' },
  { path: '/india/fixed-to-floating-home-loan-calculator/', name: 'Fixed to Floating Home Loan', country: 'India', topic: 'loans', desc: 'Compare a fixed or hybrid home loan with a floating rate.', tags: 'fixed floating hybrid home loan repo rate emi reset switch interest' },
  { path: '/india/home-loan-balance-transfer-calculator/', name: 'Home Loan Balance Transfer', country: 'India', topic: 'loans', desc: 'See if moving to a new lender saves money after fees.', tags: 'home loan balance transfer takeover refinance switch lender emi' },
  { path: '/india/home-loan-prepayment-calculator/', name: 'Home Loan Prepayment', country: 'India', topic: 'loans', desc: 'Compare a lower EMI with a shorter tenure after a part-payment.', tags: 'home loan prepayment part payment foreclosure reduce emi tenure' },
  { path: '/india/loan-comparison/', name: 'Loan Comparison', country: 'India', topic: 'loans', desc: 'Compare three bank loan offers side by side.', tags: 'loan compare bank emi interest home car offers' },
  { path: '/uae/mortgage-affordability-calculator/', name: 'Mortgage Affordability', country: 'UAE', topic: 'loans', desc: 'See what your salary, debts and savings let you buy.', tags: 'mortgage affordability how much can i borrow dbr debt burden ratio salary ltv down payment' },
  { path: '/uae/fixed-to-floating-mortgage-calculator/', name: 'Fixed to Floating Mortgage', country: 'UAE', topic: 'loans', desc: 'See your payment when a fixed rate reverts to EIBOR plus margin.', tags: 'fixed floating variable mortgage eibor margin dubai home loan reversion' },
  { path: '/uae/mortgage-buyout-calculator/', name: 'Mortgage Buyout', country: 'UAE', topic: 'loans', desc: 'See if moving to another bank saves money after fees.', tags: 'mortgage buyout loan takeover refinance balance transfer switch bank early settlement' },
  { path: '/uae/mortgage-early-repayment-calculator/', name: 'Mortgage Early Repayment', country: 'UAE', topic: 'loans', desc: 'See how much a partial settlement saves after fees.', tags: 'mortgage early repayment partial settlement prepayment overpay' },
  { path: '/uk/mortgage-calculator/', name: 'Mortgage Calculator', country: 'UK', topic: 'loans', desc: 'Estimate your monthly UK mortgage payment.', tags: 'mortgage home loan monthly repayment remortgage' },
  { path: '/us/mortgage-calculator/', name: 'Mortgage Calculator', country: 'US', topic: 'loans', desc: 'Estimate your monthly home loan payment.', tags: 'mortgage home loan monthly payment 30 year' },

  // Investing and retirement
  { path: '/india/sip-calculator/', name: 'SIP Calculator', country: 'India', topic: 'invest', desc: 'Project the returns on a monthly mutual fund investment.', tags: 'sip mutual fund investment monthly systematic' },
  { path: '/india/step-up-sip-calculator/', name: 'Step-Up SIP', country: 'India', topic: 'invest', desc: 'See how raising your SIP each year adds to your wealth.', tags: 'sip step up increase annual mutual fund' },
  { path: '/india/lumpsum-calculator/', name: 'Lump Sum', country: 'India', topic: 'invest', desc: 'Project the returns on a one-time mutual fund investment.', tags: 'lumpsum lump sum one time investment compound' },
  { path: '/india/swp-calculator/', name: 'SWP Calculator', country: 'India', topic: 'invest', desc: 'Plan monthly withdrawals and see how long your corpus lasts.', tags: 'swp systematic withdrawal plan retirement income monthly payout corpus' },
  { path: '/india/fire-calculator/', name: 'FIRE Calculator', country: 'India', topic: 'invest', desc: 'Find out when you could retire early.', tags: 'fire retire early financial independence' },
  { path: '/india/ppf-calculator/', name: 'PPF Calculator', country: 'India', topic: 'invest', desc: 'Work out your PPF maturity value over 15 years or more.', tags: 'ppf public provident fund government savings' },
  { path: '/india/nps-calculator/', name: 'NPS Calculator', country: 'India', topic: 'invest', desc: 'Estimate your NPS corpus, lump sum and monthly pension.', tags: 'nps national pension system retirement annuity lump sum pension' },
  { path: '/india/epf-calculator/', name: 'EPF Calculator', country: 'India', topic: 'invest', desc: 'Estimate your provident fund balance at retirement.', tags: 'epf pf provident fund retirement employer contribution eps interest' },
  { path: '/india/fd-calculator/', name: 'FD Calculator', country: 'India', topic: 'invest', desc: 'Work out your fixed deposit maturity amount and interest.', tags: 'fd fixed deposit bank interest maturity' },
  { path: '/uk/isa-calculator/', name: 'ISA Calculator', country: 'UK', topic: 'invest', desc: 'Project tax-free growth in a Stocks and Shares ISA.', tags: 'isa stocks shares tax free allowance' },
  { path: '/uk/pension-calculator/', name: 'Pension Calculator', country: 'UK', topic: 'invest', desc: 'Project your pension pot at retirement.', tags: 'pension retirement pot contributions' },
  { path: '/uk/savings-calculator/', name: 'Savings Calculator', country: 'UK', topic: 'invest', desc: 'See how your savings grow with compound interest.', tags: 'savings compound interest cash isa' },
  { path: '/us/401k-calculator/', name: '401(k) Calculator', country: 'US', topic: 'invest', desc: 'Project your retirement balance with contributions and growth.', tags: '401k retirement employer match' },
  { path: '/us/roth-ira-calculator/', name: 'Roth IRA', country: 'US', topic: 'invest', desc: 'Project tax-free retirement growth.', tags: 'roth ira retirement tax free' },
  { path: '/us/investment-calculator/', name: 'Investment Calculator', country: 'US', topic: 'invest', desc: 'Project long-term growth in a brokerage account.', tags: 'investment brokerage growth stocks' },
  { path: '/us/compound-interest-calculator/', name: 'Compound Interest', country: 'US', topic: 'invest', desc: 'See how compounding frequency changes your growth.', tags: 'compound interest savings growth' },
  { path: '/us/savings-calculator/', name: 'Savings Calculator', country: 'US', topic: 'invest', desc: 'See how your savings grow over time.', tags: 'savings high yield interest' },

  // Tax and salary
  { path: '/india/income-tax-calculator/', name: 'Income Tax', country: 'India', topic: 'tax', desc: 'See slab-wise tax under the new regime.', tags: 'income tax slab new regime' },
  { path: '/india/old-vs-new-tax-regime/', name: 'Old vs New Tax Regime', country: 'India', topic: 'tax', desc: 'Enter your deductions and see which regime saves more.', tags: 'tax regime old new compare deductions 80c hra' },
  { path: '/india/in-hand-salary-calculator/', name: 'In-Hand Salary', country: 'India', topic: 'tax', desc: 'Convert CTC to monthly take-home pay.', tags: 'salary in hand take home ctc net pay pf professional tax payslip' },
  { path: '/india/hra-calculator/', name: 'HRA Exemption', country: 'India', topic: 'tax', desc: 'Work out your tax-free house rent allowance.', tags: 'hra house rent allowance exemption tax rent metro bengaluru pune hyderabad ahmedabad old regime' },
  { path: '/india/capital-gains-calculator/', name: 'Capital Gains Tax', country: 'India', topic: 'tax', desc: 'Work out LTCG and STCG on shares, funds, property and gold.', tags: 'capital gains tax ltcg stcg shares mutual fund property gold indexation cii' },
  { path: '/india/gst-calculator/', name: 'GST Calculator', country: 'India', topic: 'tax', desc: 'Add or remove GST, and split it into CGST and SGST or IGST.', tags: 'gst goods services tax cgst sgst igst add remove inclusive exclusive' },
  { path: '/uae/gratuity-calculator/', name: 'UAE Gratuity', country: 'UAE', topic: 'tax', desc: 'Work out your end-of-service benefit under UAE labour law.', tags: 'gratuity end of service dubai labour law' },
  { path: '/uae/vat-calculator/', name: 'UAE VAT', country: 'UAE', topic: 'tax', desc: 'Add or extract 5% UAE VAT from any amount.', tags: 'vat tax 5 percent' },

  // Property
  { path: '/uae/dubai-property-purchase-cost-calculator/', name: 'Dubai Purchase Costs', country: 'UAE', topic: 'property', desc: 'Add up DLD, agent and mortgage costs to see the cash you need.', tags: 'dubai property purchase cost dld fee transfer trustee agent commission mortgage registration down payment' },
  { path: '/uae/rental-yield-calculator/', name: 'Dubai Rental Yield', country: 'UAE', topic: 'property', desc: 'Work out net yield after fees, service charges and vacancy.', tags: 'rental yield dubai property roi' },
  { path: '/uae/rent-vs-buy-calculator/', name: 'Rent vs Buy', country: 'UAE', topic: 'property', desc: 'Compare buying with renting and investing the difference.', tags: 'rent vs buy renting buying dubai abu dhabi home property break even' },
  { path: '/india/rent-vs-buy-calculator/', name: 'Rent vs Buy', country: 'India', topic: 'property', desc: 'Compare buying with renting and investing the difference.', tags: 'rent vs buy renting buying home house sip invest break even' },

  // Other loans and transfers
  { path: '/uae/aed-to-inr-remittance-calculator/', name: 'AED to INR Remittance', country: 'UAE', topic: 'other', desc: 'Compare rates and fees to see which provider delivers the most rupees.', tags: 'aed inr remittance send money india exchange rate dirham rupee transfer exchange house' },
  { path: '/uk/personal-loan-calculator/', name: 'Personal Loan', country: 'UK', topic: 'other', desc: 'Estimate monthly payments on an unsecured UK loan.', tags: 'personal loan unsecured monthly' },
  { path: '/us/personal-loan-calculator/', name: 'Personal Loan', country: 'US', topic: 'other', desc: 'Estimate monthly payments on an unsecured loan.', tags: 'personal loan debt consolidation monthly' },
  { path: '/us/auto-loan-calculator/', name: 'Auto Loan', country: 'US', topic: 'other', desc: 'See your monthly car payment.', tags: 'auto car loan monthly payment' },
  { path: '/us/student-loan-calculator/', name: 'Student Loan', country: 'US', topic: 'other', desc: 'Estimate federal and private student loan payments.', tags: 'student loan federal private payment' },
];
