from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING
from equipment_types import EquipmentType

import color
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity, Actor, Item

class Action:
    def __init__(self, entity: Actor) -> None:
        #super().__init__() # Why is this necessary? Action is not a subclass of anything, so this just instantiates a general object (which is done anyway)?
        self.entity = entity

    @property
    def engine(self) -> Engine:
        """Return the engine this action belongs to"""
        return self.entity.gamemap.engine

    def perform(self) -> None:
        """Perform this action with the objects needed to determine its scope.

        `self.engine` is the scope this action is being performed in.

        `self.entity` is the object performing the action

        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()

class PickupAction(Action):
    """Pickup an item and add it to the inventory, if there is room for it."""
    
    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in self.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise exceptions.Impossible("Your inventory is full.")
                
                self.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                self.engine.message_log.add_message(f"You pick up the {item.name}.")
                return
        
        raise exceptions.Impossible("There is nothing here to pick up.")

class ItemAction(Action):
    def __init__(
        self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination"""
        return self.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)

class DropAction(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            if self.item.equippable.equipment_type == EquipmentType.ARMOR:
                self.engine.message_log.add_message(
                    "You cannot drop something you are wearing.", color.invalid
                )
            else:
                self.entity.equipment.toggle_equip(self.item)
                self.entity.inventory.drop(self.item)
        else:
            self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)

class WaitAction(Action):
    def perform(self) -> None:
        pass

class TakeStairsAction(Action):
    def __init__(self, entity: Actor, downward: bool):
        super().__init__(entity)
        self.downward = downward

    def perform(self) -> None:
        """
        Take the stiars, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            if self.downward:
                if self.engine.game_world.next_floor_exists():
                    self.engine.game_world.descend_floor()
                else:
                    self.engine.game_world.generate_floor()
                self.engine.message_log.add_message(
                    "You descend the staircase.", color.descend
                )
            else:
                # TODO : implement an input "lockout" so this message does not appear when going up a staircase
                # then appearing on the down staircase on the previous floor
                raise exceptions.Impossible("You cannot go up this staircase.")

        if (self.entity.x, self.entity.y) == self.engine.game_map.upstairs_location:
            if self.downward:
                # TODO : implement an input "lockout" so this message does not appear when going down a staircase
                # then appearing on the up staircase on the next floor
                pass # raise exceptions.Impossible("You cannot go down this staircase.")
            else:
                if self.engine.game_world.current_floor_number == 1:
                    raise exceptions.Impossible("You have not finished your mission. You may not leave.")
                else:
                    self.engine.game_world.ascend_floor()
                    self.engine.message_log.add_message(
                        "You ascend the staircase.", color.descend
                    )

class ActionWithDirection(Action):
    def __init__(self, entity: Entity, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy
    
    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy
    
    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this actions destination."""
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()

class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        target = self.target_actor
        if not target:
            raise exceptions.Impossible("Nothing to attack")

        damage = self.entity.fighter.power - target.fighter.defense

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage
        else:
            self.engine.message_log.add_message(
                f"{attack_desc} but does no damage.", attack_color
            )

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            # destination is out of bounds
            raise exceptions.Impossible("That way is blocked.")
        if not self.engine.game_map.tiles[dest_x, dest_y]["walkable"]:
            # destination is blocked by a tile
            raise exceptions.Impossible("That way is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # destination is blocked by a movement-blocking entity
            raise exceptions.Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()