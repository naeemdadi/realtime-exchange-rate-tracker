import { POPULAR_CURRENCIES } from '../constants/config'
import { TABLE_COPY } from '../constants/copy'
import { currencyName, formatRate } from '../lib/format'

interface RatesTableProps {
  base: string
  rates: Record<string, number>
}

export function RatesTable({ base, rates }: RatesTableProps) {
  const codes = POPULAR_CURRENCIES.filter((code) => code !== base && rates[code] !== undefined)

  return (
    <section className="card" aria-labelledby="rates-title">
      <h2 id="rates-title">{TABLE_COPY.title}</h2>
      <table className="rates-table">
        <thead>
          <tr>
            <th scope="col">{TABLE_COPY.currencyColumn}</th>
            <th scope="col">{TABLE_COPY.rateColumn(base)}</th>
          </tr>
        </thead>
        <tbody>
          {codes.map((code) => (
            <tr key={code}>
              <th scope="row">
                <span className="code">{code}</span> {currencyName(code)}
              </th>
              <td>{formatRate(rates[code])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
