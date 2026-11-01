import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test } from 'vitest'
import App from './App'
import { failingRatesHandler, server } from './test/server'

test('user sees fresh rates, unlocks history on Paid, then keeps last known rates when the API fails', async () => {
  const user = userEvent.setup()
  render(<App />)
  const freshness = () => screen.getByRole('status', { name: 'Data freshness' })

  expect(freshness()).toHaveTextContent(/connecting/i)
  const euroRow = await screen.findByRole('row', { name: /EUR Euro/ })
  expect(within(euroRow).getByRole('cell')).toHaveTextContent('0.9')
  expect(freshness()).toHaveTextContent(/updated \d+s ago via coinbase/i)

  // Free: history is behind an upgrade prompt and the chart is hidden from assistive tech.
  expect(screen.getByRole('heading', { name: /see 30-day trends with paid/i })).toBeInTheDocument()
  expect(screen.queryByRole('img', { name: /30-day USD to EUR trend/i })).not.toBeInTheDocument()

  await user.click(screen.getByRole('button', { name: /try paid/i }))
  expect(screen.getByRole('button', { name: 'Paid (demo)' })).toHaveAttribute('aria-pressed', 'true')
  await waitFor(() => expect(freshness()).toHaveTextContent(/via premium feed/i))
  expect(await screen.findByRole('img', { name: /30-day USD to EUR trend/i })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /see 30-day trends with paid/i })).not.toBeInTheDocument()

  // API goes down: switching base still works from the last known rates, with a clear warning.
  server.use(failingRatesHandler)
  await user.selectOptions(screen.getByRole('combobox', { name: /base currency/i }), 'EUR')
  expect(await screen.findByText(/can't reach the rates service/i)).toBeInTheDocument()
  const dollarRow = screen.getByRole('row', { name: /USD US Dollar/ })
  expect(within(dollarRow).getByRole('cell')).toHaveTextContent('1.1111')
})
