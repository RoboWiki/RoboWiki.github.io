import type { ReactNode } from 'react'

import * as ReactDOMReal from 'react-dom-real'

type Container = Element | Document
type Root = { render: (node: ReactNode) => void; unmount: () => void }

const roots = new WeakMap<Container, Root>()

/**
 * React 19 删除了 ReactDOM.render / findDOMNode，
 * 但 Taro 4.3.2 的 H5 运行时仍按 React 17/18 的方式挂载。
 * H5 构建时用 webpack alias 把 react-dom 指到这里，补回旧 API。
 *
 * react-dom/client 必须惰性 require：它内部又 require('react-dom')，
 * 顶层引入会形成 shim -> client -> shim 的循环，拿到空命名空间。
 */
function client(): typeof import('react-dom/client') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return require('react-dom/client') as typeof import('react-dom/client')
}

export * from 'react-dom-real'

export function render(element: ReactNode, container: Container, callback?: () => void): Root {
  let root = roots.get(container)
  if (!root) {
    root = client().createRoot(container) as Root
    roots.set(container, root)
  }
  root.render(element)
  if (callback) setTimeout(callback, 0)
  return root
}

export function hydrate(element: ReactNode, container: Container, callback?: () => void): Root {
  let root = roots.get(container)
  if (!root) {
    root = client().hydrateRoot(container, element) as unknown as Root
    roots.set(container, root)
  } else {
    root.render(element)
  }
  if (callback) setTimeout(callback, 0)
  return root
}

export function unmountComponentAtNode(container: Container): boolean {
  const root = roots.get(container)
  if (!root) return false
  root.unmount()
  roots.delete(container)
  return true
}

export function findDOMNode(instance: unknown): Element | null {
  if (!instance) return null
  if (instance instanceof Element) return instance
  const fiber =
    (instance as { _reactInternals?: unknown; _reactInternalFiber?: unknown })._reactInternals ||
    (instance as { _reactInternalFiber?: unknown })._reactInternalFiber
  const stack: unknown[] = fiber ? [fiber] : []
  while (stack.length) {
    const node = stack.pop() as {
      stateNode?: unknown
      child?: unknown
      sibling?: unknown
    } | null
    if (!node) continue
    if (node.stateNode instanceof Element) return node.stateNode
    if (node.child) stack.push(node.child)
    if (node.sibling) stack.push(node.sibling)
  }
  return null
}

export default {
  ...ReactDOMReal,
  render,
  hydrate,
  unmountComponentAtNode,
  findDOMNode,
}
