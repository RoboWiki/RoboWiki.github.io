/**
 * ds-pet 懒加载挂载器。
 * 只在需要时下载组件与 WebP 精灵图；全局向导由 SitePet 控制，不再向空态重复注入。
 * 素材与许可见同目录 NOTICE.md / LICENSE。
 */
(() => {
  const script = document.currentScript
  const base = ((script && script.dataset.base) || '/').replace(/\/?$/, '/')
  const asset = path => base + path
  let loading = null

  const load = () => {
    if (!loading) {
      loading = import(asset('vendor/ds-pet/web/jingjing-pet.js')).then(mod => {
        mod.registerJingjingPet()
        return mod
      })
    }
    return loading
  }

  const mount = (target, options = {}) => {
    if (!target) return Promise.resolve(null)
    if (target.dataset.petMounted) return Promise.resolve(target.querySelector('jingjing-pet'))
    target.dataset.petMounted = '1'
    const pet = document.createElement('jingjing-pet')
    pet.setAttribute('src', options.src || asset('vendor/ds-pet/codex/jingjing-spritesheet.webp'))
    pet.setAttribute('storage-key', options.storageKey || 'robowiki-jingjing')
    pet.style.setProperty('--pet-accent', 'var(--rw-primary)')
    pet.style.setProperty('--pet-text', 'var(--rw-ink)')
    pet.style.setProperty('--pet-muted', 'var(--rw-ink-3)')
    pet.style.setProperty('--pet-line', 'var(--rw-border)')
    pet.style.setProperty('--pet-surface', 'var(--rw-surface-2)')
    target.replaceChildren(pet)
    return load().then(() => pet)
  }

  window.__rwPet = { load, mount }
})()
